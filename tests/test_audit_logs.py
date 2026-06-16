class TestAuditLogs:
    async def test_audit_logs_admin_allowed(self, client, admin_headers):
        resp = await client.get("/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data

    async def test_audit_logs_analyst_allowed(self, client, analyst_headers):
        resp = await client.get("/audit-logs", headers=analyst_headers)
        assert resp.status_code == 200

    async def test_audit_logs_viewer_forbidden(self, client, viewer_headers):
        resp = await client.get("/audit-logs", headers=viewer_headers)
        assert resp.status_code == 403

    async def test_audit_logs_unauthenticated(self, client):
        resp = await client.get("/audit-logs")
        assert resp.status_code == 403

    async def test_audit_log_schema(self, client, admin_headers):
        await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        resp = await client.get("/audit-logs", headers=admin_headers)
        data = resp.json()
        if data["data"]:
            log = data["data"][0]
            assert "id" in log
            assert "user_id" in log
            assert "username" in log
            assert "action" in log
            assert "resource_type" in log
            assert "resource_id" in log
            assert "details" in log
            assert "ip_address" in log
            assert "created_at" in log

    async def test_audit_log_filter_by_action(self, client, admin_headers):
        await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        resp = await client.get("/audit-logs?action=LOGIN", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        if data["data"]:
            assert all(log["action"] == "LOGIN" for log in data["data"])

    async def test_audit_log_pagination(self, client, admin_headers):
        for _ in range(3):
            await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        resp = await client.get("/audit-logs?limit=2&offset=0", headers=admin_headers)
        data = resp.json()
        assert len(data["data"]) <= 2
