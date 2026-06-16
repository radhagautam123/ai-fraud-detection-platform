class TestMonitoring:
    async def test_system_health_unauthenticated(self, client):
        resp = await client.get("/system-health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "uptime_seconds" in data
        assert "api_version" in data

    async def test_system_health_authenticated(self, client, admin_headers):
        resp = await client.get("/system-health", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_system_metrics_unauthenticated(self, client):
        resp = await client.get("/system-metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_transactions" in data
        assert "total_predictions" in data
        assert "total_alerts" in data
        assert "fraud_count" in data
        assert "fraud_rate" in data
        assert "resolved_alerts" in data
        assert "audit_log_count" in data

    async def test_system_metrics_values(self, client, admin_headers):
        resp = await client.get("/system-metrics", headers=admin_headers)
        data = resp.json()
        assert data["total_transactions"] >= 1
        assert data["total_predictions"] >= 1
        assert data["total_alerts"] >= 1
        assert data["fraud_count"] >= 1
        assert isinstance(data["fraud_rate"], (int, float))

    async def test_legacy_metrics(self, client):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_transactions" in data
        assert "total_predictions" in data
        assert "total_alerts" in data
        assert "fraud_predictions" in data
        assert "avg_risk_score" in data
