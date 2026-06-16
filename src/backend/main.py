from datetime import datetime, timedelta
import time as time_module

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, func, case, cast, Date, text

from src.common.database import async_session, engine
from src.common.models import (
    Transaction,
    Prediction,
    Alert,
    TrainedModel,
    User,
    AuditLog,
)
from src.backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
    optional_current_user,
)
from src.backend.audit import create_audit_log

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Fraud Detection API", version="2.2.0")
_start_time = time_module.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RegisterPayload(BaseModel):
    username: str
    email: str
    password: str
    role: str = "VIEWER"

class LoginPayload(BaseModel):
    username: str
    password: str

class AssignPayload(BaseModel):
    assigned_to: int | None = None

class StatusPayload(BaseModel):
    status: str

class NotesPayload(BaseModel):
    case_notes: str

# ---------------------------------------------------------------------------
# Health / Root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "AI Fraud Detection API Running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# ---------------------------------------------------------------------------
# System Monitoring
# ---------------------------------------------------------------------------

@app.get("/system-health")
async def system_health(current_user: User | None = Depends(optional_current_user)):
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    uptime_seconds = int(time_module.time() - _start_time)

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "uptime_seconds": uptime_seconds,
        "uptime_human": str(timedelta(seconds=uptime_seconds)),
        "api_version": "2.2.0",
    }

@app.get("/system-metrics")
async def system_metrics(current_user: User | None = Depends(optional_current_user)):
    async with async_session() as session:
        total_transactions = await session.scalar(select(func.count()).select_from(Transaction))
        total_predictions = await session.scalar(select(func.count()).select_from(Prediction))
        total_alerts = await session.scalar(select(func.count()).select_from(Alert))
        fraud_count = await session.scalar(
            select(func.count()).select_from(Prediction).where(Prediction.is_fraud == True)
        )
        resolved = await session.scalar(
            select(func.count()).select_from(Alert).where(Alert.investigation_status == "CLOSED")
        )
        audit_count = await session.scalar(select(func.count()).select_from(AuditLog))

        fraud_rate = round((fraud_count / total_predictions * 100), 2) if total_predictions else 0.0

        return {
            "total_transactions": total_transactions or 0,
            "total_predictions": total_predictions or 0,
            "total_alerts": total_alerts or 0,
            "fraud_count": fraud_count or 0,
            "fraud_rate": fraud_rate,
            "resolved_alerts": resolved or 0,
            "audit_log_count": audit_count or 0,
        }

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/auth/register")
async def register(payload: RegisterPayload, request: Request):
    async with async_session() as session:
        existing = await session.execute(
            select(User).where(
                (User.username == payload.username) | (User.email == payload.email)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username or email already exists")

        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role.upper(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }

@app.post("/auth/login")
async def login(payload: LoginPayload, request: Request):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == payload.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")

        token = create_access_token({"sub": user.username, "role": user.role})

        ip = request.client.host if request.client else None
        await create_audit_log(user, "LOGIN", details=f"User {user.username} logged in", ip_address=ip)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }

@app.get("/users/me")
async def users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }

@app.get("/users")
async def list_users(current_user: User = Depends(require_role("ADMIN", "ANALYST"))):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        return [
            {"id": u.id, "username": u.username, "email": u.email, "role": u.role}
            for u in users
        ]

# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

@app.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    action: str = None,
    current_user: User = Depends(require_role("ADMIN", "ANALYST")),
):
    async with async_session() as session:
        query = select(AuditLog)
        if action:
            query = query.where(AuditLog.action == action.upper())

        count_result = await session.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        result = await session.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()

        return {
            "total": total or 0,
            "data": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": str(log.created_at),
                }
                for log in rows
            ],
        }

# ---------------------------------------------------------------------------
# Metrics (legacy, used by dashboards)
# ---------------------------------------------------------------------------

@app.get("/metrics")
async def metrics(current_user: User | None = Depends(optional_current_user)):
    async with async_session() as session:
        total_transactions = await session.scalar(select(func.count()).select_from(Transaction))
        total_predictions = await session.scalar(select(func.count()).select_from(Prediction))
        total_alerts = await session.scalar(select(func.count()).select_from(Alert))
        fraud_predictions = await session.scalar(
            select(func.count()).select_from(Prediction).where(Prediction.is_fraud == True)
        )
        avg_risk_score = await session.scalar(select(func.avg(Prediction.risk_score)))

        return {
            "total_transactions": total_transactions or 0,
            "total_predictions": total_predictions or 0,
            "total_alerts": total_alerts or 0,
            "fraud_predictions": fraud_predictions or 0,
            "avg_risk_score": round(float(avg_risk_score or 0), 2),
        }

# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@app.get("/alerts")
async def alerts(
    limit: int = 20,
    offset: int = 0,
    status: str = None,
    risk_tier: str = None,
    investigation_status: str = None,
    date_from: str = None,
    date_to: str = None,
    current_user: User | None = Depends(optional_current_user),
):
    async with async_session() as session:
        query = select(Alert)

        if status:
            query = query.where(Alert.alert_status == status.upper())
        if risk_tier:
            query = query.where(Alert.risk_tier == risk_tier.upper())
        if investigation_status:
            query = query.where(Alert.investigation_status == investigation_status.upper())
        if date_from:
            query = query.where(Alert.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.where(Alert.created_at <= datetime.fromisoformat(date_to))

        count_result = await session.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        result = await session.execute(
            query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()

        return {
            "total": total or 0,
            "data": [
                {
                    "alert_id": a.alert_id,
                    "risk_tier": a.risk_tier,
                    "status": a.alert_status,
                    "investigation_status": a.investigation_status,
                    "assigned_to": a.assigned_to,
                    "created_at": str(a.created_at),
                    "updated_at": str(a.updated_at) if a.updated_at else None,
                }
                for a in rows
            ],
        }

@app.get("/alerts/{alert_id}")
async def alert_detail(
    alert_id: int,
    current_user: User | None = Depends(optional_current_user),
):
    async with async_session() as session:
        result = await session.execute(
            select(Alert, Prediction, Transaction)
            .join(Prediction, Alert.prediction_id == Prediction.prediction_id)
            .join(Transaction, Prediction.transaction_id == Transaction.transaction_id)
            .where(Alert.alert_id == alert_id)
        )
        row = result.one_or_none()
        if not row:
            return {}

        alert, prediction, transaction = row

        assigned_user = None
        if alert.assigned_to:
            u_result = await session.execute(select(User).where(User.id == alert.assigned_to))
            u = u_result.scalar_one_or_none()
            if u:
                assigned_user = {"id": u.id, "username": u.username, "role": u.role}

        return {
            "alert_id": alert.alert_id,
            "risk_tier": alert.risk_tier,
            "status": alert.alert_status,
            "investigation_status": alert.investigation_status,
            "assigned_to": alert.assigned_to,
            "assigned_user": assigned_user,
            "case_notes": alert.case_notes,
            "resolution": alert.resolution,
            "resolved_at": str(alert.resolved_at) if alert.resolved_at else None,
            "created_at": str(alert.created_at),
            "updated_at": str(alert.updated_at) if alert.updated_at else None,
            "prediction_id": prediction.prediction_id,
            "fraud_probability": prediction.fraud_probability,
            "risk_score": prediction.risk_score,
            "is_fraud": prediction.is_fraud,
            "model_version": prediction.model_version,
            "prediction_timestamp": str(prediction.prediction_timestamp),
            "transaction_id": transaction.transaction_id,
            "amount": float(transaction.amount),
            "merchant": transaction.merchant,
            "category": transaction.category,
            "card_holder_id": transaction.card_holder_id,
            "transaction_timestamp": str(transaction.timestamp),
        }

# ---------------------------------------------------------------------------
# Case Management
# ---------------------------------------------------------------------------

@app.patch("/alerts/{alert_id}/assign")
async def assign_alert(
    alert_id: int,
    payload: AssignPayload,
    request: Request,
    current_user: User = Depends(require_role("ADMIN", "ANALYST")),
):
    async with async_session() as session:
        result = await session.execute(select(Alert).where(Alert.alert_id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        old = alert.assigned_to
        alert.assigned_to = payload.assigned_to
        if payload.assigned_to and alert.investigation_status == "NEW":
            alert.investigation_status = "ASSIGNED"
        alert.updated_at = datetime.utcnow()
        await session.commit()

    assigned_username = None
    if payload.assigned_to:
        async with async_session() as s:
            u = (await s.execute(select(User).where(User.id == payload.assigned_to))).scalar_one_or_none()
            if u:
                assigned_username = u.username

    ip = request.client.host if request.client else None
    await create_audit_log(
        current_user, "ALERT_ASSIGN",
        resource_type="alert", resource_id=alert_id,
        details=f"Assigned alert #{alert_id} to {assigned_username or 'unassigned'} (was {old})",
        ip_address=ip,
    )

    return {"assigned_to": alert.assigned_to, "investigation_status": alert.investigation_status}

@app.patch("/alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    payload: StatusPayload,
    request: Request,
    current_user: User = Depends(require_role("ADMIN", "ANALYST")),
):
    valid = {"NEW", "ASSIGNED", "INVESTIGATING", "CONFIRMED_FRAUD", "FALSE_POSITIVE", "CLOSED"}
    if payload.status.upper() not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid}")

    async with async_session() as session:
        result = await session.execute(select(Alert).where(Alert.alert_id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        old = alert.investigation_status
        alert.investigation_status = payload.status.upper()
        alert.alert_status = payload.status.upper()
        alert.updated_at = datetime.utcnow()
        await session.commit()

    ip = request.client.host if request.client else None
    await create_audit_log(
        current_user, "ALERT_STATUS_CHANGE",
        resource_type="alert", resource_id=alert_id,
        details=f"Changed alert #{alert_id} status: {old} -> {payload.status.upper()}",
        ip_address=ip,
    )

    return {"investigation_status": alert.investigation_status, "alert_status": alert.alert_status}

@app.patch("/alerts/{alert_id}/notes")
async def update_alert_notes(
    alert_id: int,
    payload: NotesPayload,
    request: Request,
    current_user: User = Depends(require_role("ADMIN", "ANALYST")),
):
    async with async_session() as session:
        result = await session.execute(select(Alert).where(Alert.alert_id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        old_len = len(alert.case_notes) if alert.case_notes else 0
        alert.case_notes = payload.case_notes
        alert.updated_at = datetime.utcnow()
        await session.commit()

    ip = request.client.host if request.client else None
    await create_audit_log(
        current_user, "ALERT_NOTE_UPDATED",
        resource_type="alert", resource_id=alert_id,
        details=f"Updated notes on alert #{alert_id} ({old_len} chars -> {len(payload.case_notes)} chars)",
        ip_address=ip,
    )

    return {"case_notes": alert.case_notes}

@app.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    payload: StatusPayload,
    request: Request,
    current_user: User = Depends(require_role("ADMIN", "ANALYST")),
):
    valid = {"CONFIRMED_FRAUD", "FALSE_POSITIVE"}
    if payload.status.upper() not in valid:
        raise HTTPException(status_code=400, detail="Resolution must be CONFIRMED_FRAUD or FALSE_POSITIVE")

    async with async_session() as session:
        result = await session.execute(select(Alert).where(Alert.alert_id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert.resolution = payload.status.upper()
        alert.investigation_status = "CLOSED"
        alert.alert_status = "CLOSED"
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        await session.commit()

    ip = request.client.host if request.client else None
    await create_audit_log(
        current_user, "ALERT_RESOLVED",
        resource_type="alert", resource_id=alert_id,
        details=f"Resolved alert #{alert_id} as {payload.status.upper()}",
        ip_address=ip,
    )

    return {
        "resolution": alert.resolution,
        "investigation_status": alert.investigation_status,
        "resolved_at": str(alert.resolved_at),
    }

# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@app.get("/transactions")
async def transactions(
    limit: int = 20,
    offset: int = 0,
    search: str = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    current_user: User | None = Depends(optional_current_user),
):
    async with async_session() as session:
        sort_col = {
            "timestamp": Transaction.timestamp,
            "amount": Transaction.amount,
            "merchant": Transaction.merchant,
        }.get(sort_by, Transaction.timestamp)

        order_fn = sort_col.desc if sort_order == "desc" else sort_col.asc

        query = select(Transaction)

        if search:
            query = query.where(
                Transaction.merchant.ilike(f"%{search}%")
                | Transaction.transaction_id.ilike(f"%{search}%")
                | Transaction.category.ilike(f"%{search}%")
            )

        count_result = await session.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        result = await session.execute(query.order_by(order_fn()).offset(offset).limit(limit))
        rows = result.scalars().all()

        return {
            "total": total or 0,
            "data": [
                {
                    "transaction_id": t.transaction_id,
                    "amount": float(t.amount),
                    "merchant": t.merchant,
                    "category": t.category,
                    "card_holder_id": t.card_holder_id,
                    "timestamp": str(t.timestamp),
                }
                for t in rows
            ],
        }

# ---------------------------------------------------------------------------
# Charts / Analytics
# ---------------------------------------------------------------------------

@app.get("/risk-distribution")
async def risk_distribution(current_user: User | None = Depends(optional_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(Alert.risk_tier, func.count(Alert.alert_id)).group_by(Alert.risk_tier)
        )
        return {row[0]: row[1] for row in result.all()}

@app.get("/model-info")
async def model_info(current_user: User | None = Depends(optional_current_user)):
    async with async_session() as session:
        model = (await session.execute(select(TrainedModel).limit(1))).scalars().first()
        if not model:
            return {}
        return {
            "version": model.model_version,
            "algorithm": model.algorithm,
            "auc_roc": model.auc_roc,
            "f1_score": model.f1_score,
        }

@app.get("/fraud-trend")
async def fraud_trend(
    period: str = "day",
    limit: int = 30,
    current_user: User | None = Depends(optional_current_user),
):
    async with async_session() as session:
        date_expr = func.date_trunc("hour", Alert.created_at) if period == "hour" else cast(Alert.created_at, Date)
        result = await session.execute(
            select(date_expr.label("date"), func.count(Alert.alert_id))
            .group_by(date_expr)
            .order_by(date_expr.desc())
            .limit(limit)
        )
        rows = result.all()
        return [{"date": str(row[0]), "count": row[1]} for row in reversed(rows)]

@app.get("/top-merchants")
async def top_merchants(limit: int = 10, current_user: User | None = Depends(optional_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(Transaction.merchant, func.count(Transaction.transaction_id))
            .join(Prediction, Transaction.transaction_id == Prediction.transaction_id)
            .where(Prediction.is_fraud == True)
            .group_by(Transaction.merchant)
            .order_by(func.count(Transaction.transaction_id).desc())
            .limit(limit)
        )
        return [{"merchant": row[0], "count": row[1]} for row in result.all()]

@app.get("/risk-score-distribution")
async def risk_score_distribution(current_user: User | None = Depends(optional_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(
                case(
                    (Prediction.risk_score <= 39, "Low"),
                    (Prediction.risk_score <= 69, "Medium"),
                    (Prediction.risk_score <= 89, "High"),
                    else_="Critical",
                ).label("bucket"),
                func.count(Prediction.prediction_id),
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        return [{"bucket": row[0], "count": row[1]} for row in result.all()]
