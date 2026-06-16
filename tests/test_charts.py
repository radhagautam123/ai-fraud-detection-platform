class TestCharts:
    async def test_risk_distribution(self, client):
        resp = await client.get("/risk-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    async def test_model_info(self, client):
        resp = await client.get("/model-info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"
        assert data["algorithm"] == "XGBoost"
        assert data["auc_roc"] == 0.98
        assert data["f1_score"] == 0.94

    async def test_fraud_trend(self, client):
        resp = await client.get("/fraud-trend?period=hour&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_top_merchants(self, client):
        resp = await client.get("/top-merchants?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "merchant" in data[0]
            assert "count" in data[0]

    async def test_risk_score_distribution(self, client):
        resp = await client.get("/risk-score-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_transactions(self, client):
        resp = await client.get("/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data
        assert len(data["data"]) >= 1

    async def test_transactions_with_search(self, client):
        resp = await client.get("/transactions?search=TestMerchant")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_transactions_with_sort(self, client):
        resp = await client.get("/transactions?sort_by=amount&sort_order=asc")
        assert resp.status_code == 200
