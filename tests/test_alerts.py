import pytest


class TestAlerts:
    async def test_list_alerts_unauthenticated(self, client):
        resp = await client.get("/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data

    async def test_list_alerts_authenticated(self, client, admin_headers):
        resp = await client.get("/alerts", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_alert_detail(self, client, admin_headers):
        resp = await client.get("/alerts/1", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["alert_id"] == 1
        assert data["risk_tier"] == "HIGH"

    async def test_alert_detail_not_found(self, client, admin_headers):
        resp = await client.get("/alerts/9999", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == {}

    async def test_assign_alert(self, client, admin_headers):
        resp = await client.patch("/alerts/1/assign", json={"assigned_to": 1}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["assigned_to"] == 1

    async def test_assign_alert_viewer_forbidden(self, client, viewer_headers):
        resp = await client.patch("/alerts/1/assign", json={"assigned_to": 1}, headers=viewer_headers)
        assert resp.status_code == 403

    async def test_update_status(self, client, admin_headers):
        resp = await client.patch("/alerts/1/status", json={"status": "INVESTIGATING"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["investigation_status"] == "INVESTIGATING"

    async def test_update_status_invalid(self, client, admin_headers):
        resp = await client.patch("/alerts/1/status", json={"status": "BOGUS"}, headers=admin_headers)
        assert resp.status_code == 400

    async def test_update_notes(self, client, admin_headers):
        resp = await client.patch("/alerts/1/notes", json={"case_notes": "Investigated thoroughly"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["case_notes"] == "Investigated thoroughly"

    async def test_resolve_alert_confirm_fraud(self, client, admin_headers):
        resp = await client.patch("/alerts/1/resolve", json={"status": "CONFIRMED_FRAUD"}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution"] == "CONFIRMED_FRAUD"
        assert data["investigation_status"] == "CLOSED"

    async def test_resolve_alert_false_positive(self, client, admin_headers):
        resp = await client.patch("/alerts/1/resolve", json={"status": "FALSE_POSITIVE"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["resolution"] == "FALSE_POSITIVE"

    async def test_resolve_alert_invalid_resolution(self, client, admin_headers):
        resp = await client.patch("/alerts/1/resolve", json={"status": "CLOSED"}, headers=admin_headers)
        assert resp.status_code == 400

    async def test_assign_nonexistent_alert(self, client, admin_headers):
        resp = await client.patch("/alerts/9999/assign", json={"assigned_to": 1}, headers=admin_headers)
        assert resp.status_code == 404
