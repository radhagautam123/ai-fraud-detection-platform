import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from config.settings import settings
settings.DATABASE_URL = os.environ["DATABASE_URL"]

from src.common.database import engine, async_session
from src.common.models import Base, User, TrainedModel, Transaction, Prediction, Alert
from src.backend.main import app
from src.backend.auth import hash_password, create_access_token


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        users = {
            "admin": User(username="admin", email="admin@test.com",
                          hashed_password=hash_password("admin123"), role="ADMIN"),
            "analyst": User(username="analyst", email="analyst@test.com",
                            hashed_password=hash_password("analyst123"), role="ANALYST"),
            "viewer": User(username="viewer", email="viewer@test.com",
                           hashed_password=hash_password("viewer123"), role="VIEWER"),
        }
        for u in users.values():
            session.add(u)
        session.flush()

        tm = TrainedModel(model_version="1.0.0", algorithm="XGBoost",
                          auc_roc=0.98, f1_score=0.94, model_binary_path="models/test.pkl")
        session.add(tm)
        session.flush()

        t = Transaction(transaction_id="TXN001", timestamp=datetime.utcnow(),
                        card_holder_id="CH001", amount=150.00,
                        merchant="TestMerchant", category="retail")
        session.add(t)
        session.flush()

        p = Prediction(transaction_id="TXN001", model_version="1.0.0",
                       fraud_probability=0.92, risk_score=85, is_fraud=True)
        session.add(p)
        session.flush()

        a = Alert(prediction_id=p.prediction_id, risk_tier="HIGH",
                  alert_status="NEW", investigation_status="NEW")
        session.add(a)

        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _get_token(username):
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.username == username))).scalar_one()
        return create_access_token({"sub": user.username, "role": user.role})


@pytest_asyncio.fixture
async def admin_token():
    return await _get_token("admin")


@pytest_asyncio.fixture
async def analyst_token():
    return await _get_token("analyst")


@pytest_asyncio.fixture
async def viewer_token():
    return await _get_token("viewer")


@pytest_asyncio.fixture
async def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def analyst_headers(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest_asyncio.fixture
async def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}
