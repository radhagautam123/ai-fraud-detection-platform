import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.backend.main import app
from src.common.database import async_session
from src.common.models import User


class TestAuth:
    async def test_login_success(self, client):
        resp = await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "ADMIN"

    async def test_login_invalid_password(self, client):
        resp = await client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    async def test_register_new_user(self, client):
        resp = await client.post("/auth/register", json={
            "username": "newguy", "email": "new@test.com", "password": "test123", "role": "VIEWER",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newguy"
        assert data["role"] == "VIEWER"

    async def test_register_duplicate_username(self, client):
        resp = await client.post("/auth/register", json={
            "username": "viewer", "email": "unique@test.com", "password": "test123",
        })
        assert resp.status_code == 400

    async def test_register_duplicate_email(self, client):
        resp = await client.post("/auth/register", json={
            "username": "unique", "email": "viewer@test.com", "password": "test123",
        })
        assert resp.status_code == 400

    async def test_me_authenticated(self, client, admin_headers):
        resp = await client.get("/users/me", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"

    async def test_me_unauthenticated(self, client):
        resp = await client.get("/users/me")
        assert resp.status_code == 401

    async def test_list_users_admin(self, client, admin_headers):
        resp = await client.get("/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3
        usernames = [u["username"] for u in data]
        assert "admin" in usernames
        assert "analyst" in usernames
        assert "viewer" in usernames

    async def test_list_users_viewer_forbidden(self, client, viewer_headers):
        resp = await client.get("/users", headers=viewer_headers)
        assert resp.status_code == 403

    async def test_list_users_analyst_allowed(self, client, analyst_headers):
        resp = await client.get("/users", headers=analyst_headers)
        assert resp.status_code == 200

    async def test_root_endpoint(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "AI Fraud Detection API Running"

    async def test_health_endpoint(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
