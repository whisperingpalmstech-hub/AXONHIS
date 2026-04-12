import pytest
from httpx import AsyncClient
from typing import AsyncGenerator

@pytest.fixture
def analytics_client(client: AsyncClient, auth_headers: dict[str, str]) -> AsyncClient:
    """Client for testing analytics APIs with auth headers injected."""
    client.headers.update(auth_headers)
    return client

@pytest.mark.asyncio
async def test_clinical_metrics(analytics_client: AsyncClient):
    # Fetch clinical metrics
    response = await analytics_client.get("/api/v1/analytics/clinical-metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "admissions_count" in data[0]
        assert "readmission_rate" in data[0]

@pytest.mark.asyncio
async def test_financial_metrics(analytics_client: AsyncClient):
    # Fetch financial metrics
    response = await analytics_client.get("/api/v1/analytics/financial-metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "daily_revenue" in data[0]
        assert "outstanding_invoices_amount" in data[0]

@pytest.mark.asyncio
async def test_operational_metrics(analytics_client: AsyncClient):
    # Fetch operational metrics
    response = await analytics_client.get("/api/v1/analytics/operational-metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "bed_occupancy_rate" in data[0]
        assert "patient_throughput" in data[0]

@pytest.mark.asyncio
async def test_predictive_models(analytics_client: AsyncClient):
    # Fetch predictive models
    response = await analytics_client.get("/api/v1/analytics/predictions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "target_date" in data[0]
        assert "predicted_value" in data[0]

@pytest.mark.asyncio
async def test_executive_dashboard(analytics_client: AsyncClient):
    # Fetch aggregated executive dashboard
    response = await analytics_client.get("/api/v1/analytics/dashboards/executive")
    assert response.status_code == 200
    data = response.json()
    assert "daily_admissions" in data
    assert "daily_revenue" in data
    assert "bed_occupancy_rate" in data
    assert "predictions" in data
    assert isinstance(data["predictions"], list)

@pytest.mark.asyncio
async def test_analytics_reports(analytics_client: AsyncClient):
    for report_type in ["clinical", "financial", "operational"]:
        response = await analytics_client.get(f"/api/v1/analytics/reports/export?report_type={report_type}&days=1")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment; filename=" in response.headers["content-disposition"]
        # Basic sanity check that payload has CSV data
        text = response.text
        assert text.strip() != ""
