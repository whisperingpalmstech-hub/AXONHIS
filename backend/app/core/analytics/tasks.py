"""
Background aggregation jobs for Phase 10 Analytics.
These tasks are scheduled to run periodically and pre-calculate analytics data.
"""
import asyncio
from datetime import date
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker

from app.core.analytics.clinical_metrics.services import ClinicalMetricService
from app.core.analytics.financial_metrics.services import FinancialMetricService
from app.core.analytics.operational_metrics.services import OperationalMetricService
from app.core.analytics.predictive_models.services import PredictiveModelService

async def _aggregate_all_metrics():
    """Async helper to crunch metrics."""
    async with async_session_maker() as db:
        cs = ClinicalMetricService(db)
        fs = FinancialMetricService(db)
        os = OperationalMetricService(db)
        ps = PredictiveModelService(db)

        # Triggering daily aggregation routines
        await cs.aggregate_daily()
        await fs.aggregate_daily()
        await os.aggregate_daily()
        
        # Predictive models
        await ps.generate_forecasts()
        
        # Commit not strictly necessary if each aggregate does its own commit
        # but just in case we let them handle their own persistence.

@shared_task(name="axonhis.analytics.daily_crunch")
def aggregate_daily_analytics():
    """
    Run the nightly batch aggregation for clinical, 
    financial, operational metrics, and predictive forecasts.
    """
    asyncio.run(_aggregate_all_metrics())
    return {"status": "success", "date": str(date.today())}
