from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.analytics.operational_metrics.models import DailyOperationalMetric

class OperationalMetricService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_metrics(self, days: int = 30) -> list[DailyOperationalMetric]:
        result = await self.db.execute(
            select(DailyOperationalMetric).order_by(desc(DailyOperationalMetric.metric_date)).limit(days)
        )
        return list(result.scalars().all())

    async def aggregate_daily(self) -> DailyOperationalMetric:
        from datetime import date
        from sqlalchemy import select, func, cast, Date
        from app.core.encounters.encounters.models import Encounter
        from app.core.tasks.models import Task
        
        today = date.today()
        
        # 1. Bed Occupancy Rate and Patient Throughput
        # Assuming bed occupancy is calculated based on active IP encounters out of a baseline of 100 beds total
        ip_enc_q = select(func.count(Encounter.id)).where(
            Encounter.encounter_type == 'IP', 
            Encounter.status.in_(['scheduled', 'in_progress'])
        )
        ip_enc_res = await self.db.execute(ip_enc_q)
        ip_count = ip_enc_res.scalar() or 0
        occupancy_rate = min(ip_count / 100 * 100, 100.0)
        
        # Patient throughput (completed encounters today)
        throughput_q = select(func.count(Encounter.id)).where(
            Encounter.status == 'completed',
            cast(Encounter.updated_at, Date) == today
        )
        throughput_res = await self.db.execute(throughput_q)
        throughput = throughput_res.scalar() or 0
        
        # 2. Avg task completion: Just counting completed tasks for today as throughput indicator for now, unless we do full time difference
        tasks_q = select(func.count(Task.id)).where(
            Task.status == 'COMPLETED',
            cast(Task.completed_at, Date) == today
        )
        tasks_res = await self.db.execute(tasks_q)
        tasks_count_today = tasks_res.scalar() or 0
        
        # Fallback to an estimated 25 min average unless full tracking implemented
        avg_task_mins = 25.0 if tasks_count_today > 0 else 0.0
        
        result = await self.db.execute(select(DailyOperationalMetric).where(DailyOperationalMetric.metric_date == today))
        metric = result.scalars().first()
        if not metric:
            metric = DailyOperationalMetric(metric_date=today)
            self.db.add(metric)
            
        metric.bed_occupancy_rate = occupancy_rate
        metric.patient_throughput = throughput
        metric.avg_task_completion_mins = avg_task_mins
        
        metric.lab_processing_volume = 0 # Future expansion
        metric.pharmacy_dispensing_volume = 0 # Future expansion
        metric.staff_workload_index = 0.0 # Future expansion
        
        await self.db.commit()
        await self.db.refresh(metric)
        return metric
