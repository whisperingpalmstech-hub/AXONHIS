from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.analytics.clinical_metrics.models import DailyClinicalMetric

class ClinicalMetricService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_metrics(self, days: int = 30) -> list[DailyClinicalMetric]:
        result = await self.db.execute(
            select(DailyClinicalMetric).order_by(desc(DailyClinicalMetric.metric_date)).limit(days)
        )
        return list(result.scalars().all())

    async def aggregate_daily(self) -> DailyClinicalMetric:
        from datetime import date
        from sqlalchemy import select, func, cast, Date
        from app.core.encounters.encounters.models import Encounter
        from app.core.encounters.clinical_flags.models import ClinicalFlag
        
        today = date.today()
        
        # 1. Admissions count (IP encounters created today)
        adm_q = select(func.count(Encounter.id)).where(
            cast(Encounter.created_at, Date) == today,
            Encounter.encounter_type == 'IP'
        )
        adm_res = await self.db.execute(adm_q)
        admissions_count = adm_res.scalar() or 0
        
        # 2. Critical alerts count (ClinicalFlags created today)
        alerts_q = select(func.count(ClinicalFlag.id)).where(cast(ClinicalFlag.created_at, Date) == today)
        alerts_res = await self.db.execute(alerts_q)
        critical_alerts_count = alerts_res.scalar() or 0
        
        result = await self.db.execute(select(DailyClinicalMetric).where(DailyClinicalMetric.metric_date == today))
        metric = result.scalars().first()
        if not metric:
            metric = DailyClinicalMetric(metric_date=today)
            self.db.add(metric)
            
        metric.admissions_count = admissions_count
        metric.critical_alerts_count = critical_alerts_count
        # Remaining metrics kept at default/0 or simplified due to lack of complex tracking tables right now
        metric.readmission_rate = 0.0
        metric.average_los_hours = 0.0
        metric.avg_lab_turnaround_hours = 0.0
        metric.avg_alert_response_mins = 0.0
        
        await self.db.commit()
        await self.db.refresh(metric)
        return metric
