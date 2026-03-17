from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.analytics.predictive_models.models import HospitalPrediction

class PredictiveModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_predictions(self, prediction_type: str | None = None) -> list[HospitalPrediction]:
        from datetime import date, timedelta
        today = date.today()
        # Fetch predictions targetting today up to next 7 days
        query = select(HospitalPrediction).where(
            HospitalPrediction.target_date >= today,
            HospitalPrediction.target_date <= today + timedelta(days=7)
        )
        if prediction_type:
            query = query.where(HospitalPrediction.prediction_type == prediction_type)
        
        result = await self.db.execute(query.order_by(HospitalPrediction.target_date))
        return list(result.scalars().all())

    async def generate_forecasts(self):
        from datetime import date, timedelta
        from sqlalchemy import select, func, cast, Date
        from app.core.encounters.encounters.models import Encounter
        from app.core.orders.models import Order
        
        today = date.today()
        
        # Calculate naive forecasts based on the current active queues and schedules
        types = ["bed_demand", "lab_workload", "admissions", "medication_demand"]
        for t in types:
            for i in range(1, 4):
                target = today + timedelta(days=i)
                result = await self.db.execute(select(HospitalPrediction).where(
                    and_(
                        HospitalPrediction.target_date == target,
                        HospitalPrediction.prediction_type == t
                    )
                ))
                existing = result.scalars().first()
                if not existing:
                    predicted_value = 0.0
                    if t == "bed_demand":
                        # Naive: existing active IPs + scheduled IPs for that date
                        bd_q = select(func.count(Encounter.id)).where(
                            Encounter.encounter_type == 'IP',
                            Encounter.status.in_(['in_progress'])
                        )
                        bd_res = await self.db.execute(bd_q)
                        predicted_value = float(bd_res.scalar() or 0.0)
                    elif t == "lab_workload":
                        lab_q = select(func.count(Order.id)).where(
                            Order.order_type == 'lab',
                            Order.status == 'pending'
                        )
                        lab_res = await self.db.execute(lab_q)
                        predicted_value = float(lab_res.scalar() or 0.0)
                    elif t == "admissions":
                        adm_q = select(func.count(Encounter.id)).where(
                            Encounter.encounter_type == 'IP',
                            cast(Encounter.start_time, Date) == target,
                            Encounter.status == 'scheduled'
                        )
                        adm_res = await self.db.execute(adm_q)
                        predicted_value = float(adm_res.scalar() or 0.0)
                    elif t == "medication_demand":
                        med_q = select(func.count(Order.id)).where(
                            Order.order_type == 'pharmacy',
                            Order.status == 'pending'
                        )
                        med_res = await self.db.execute(med_q)
                        predicted_value = float(med_res.scalar() or 0.0)
                    
                    pred = HospitalPrediction(
                        target_date=target,
                        prediction_type=t,
                        predicted_value=predicted_value,
                        confidence_interval_low=max(0.0, predicted_value * 0.9),
                        confidence_interval_high=predicted_value * 1.1,
                        factors={"model": "naive_queue_based", "status": "active_projection"}
                    )
                    self.db.add(pred)
        await self.db.commit()
