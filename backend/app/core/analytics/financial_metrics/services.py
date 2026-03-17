from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.analytics.financial_metrics.models import DailyFinancialMetric

class FinancialMetricService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_metrics(self, days: int = 30) -> list[DailyFinancialMetric]:
        result = await self.db.execute(
            select(DailyFinancialMetric).order_by(desc(DailyFinancialMetric.metric_date)).limit(days)
        )
        return list(result.scalars().all())

    async def aggregate_daily(self) -> DailyFinancialMetric:
        from datetime import date
        from sqlalchemy import select, func, cast, Date
        from app.core.billing.invoices.models import Invoice
        from app.core.billing.insurance.models import InsuranceClaim
        from app.core.encounters.encounters.models import Encounter
        
        today = date.today()
        
        # 1. Daily revenue
        rev_q = select(func.sum(Invoice.total_amount)).where(cast(Invoice.generated_at, Date) == today)
        rev_res = await self.db.execute(rev_q)
        daily_revenue = float(rev_res.scalar() or 0.0)

        # 2. Outpatient and Inpatient revenue
        op_rev_q = select(func.sum(Invoice.total_amount)).join(Encounter, Invoice.encounter_id == Encounter.id).where(
            cast(Invoice.generated_at, Date) == today,
            Encounter.encounter_type == 'OP'
        )
        op_rev_res = await self.db.execute(op_rev_q)
        outpatient_revenue = float(op_rev_res.scalar() or 0.0)

        ip_rev_q = select(func.sum(Invoice.total_amount)).join(Encounter, Invoice.encounter_id == Encounter.id).where(
            cast(Invoice.generated_at, Date) == today,
            Encounter.encounter_type == 'IP'
        )
        ip_rev_res = await self.db.execute(ip_rev_q)
        inpatient_revenue = float(ip_rev_res.scalar() or 0.0)

        # 3. Insurance claims count
        claims_q = select(func.count(InsuranceClaim.id)).where(cast(InsuranceClaim.submitted_at, Date) == today)
        claims_res = await self.db.execute(claims_q)
        claims_count = claims_res.scalar() or 0

        # 4. claim_approval_rate
        app_claims_q = select(func.count(InsuranceClaim.id)).where(InsuranceClaim.status == 'approved')
        tot_claims_q = select(func.count(InsuranceClaim.id))
        app_claims_res = await self.db.execute(app_claims_q)
        tot_claims_res = await self.db.execute(tot_claims_q)
        app_claims_count = app_claims_res.scalar() or 0
        tot_claims_count = tot_claims_res.scalar() or 0
        approval_rate = (app_claims_count / tot_claims_count * 100) if tot_claims_count > 0 else 0.0

        # 5. Outstanding invoices amount
        out_inv_q = select(func.sum(Invoice.total_amount)).where(Invoice.status.in_(['issued', 'partially_paid']))
        out_inv_res = await self.db.execute(out_inv_q)
        outstanding_invoices_amount = float(out_inv_res.scalar() or 0.0)

        result = await self.db.execute(select(DailyFinancialMetric).where(DailyFinancialMetric.metric_date == today))
        metric = result.scalars().first()
        if not metric:
            metric = DailyFinancialMetric(metric_date=today)
            self.db.add(metric)
        
        metric.daily_revenue = daily_revenue
        metric.outpatient_revenue = outpatient_revenue
        metric.inpatient_revenue = inpatient_revenue
        metric.insurance_claims_count = claims_count
        metric.claim_approval_rate = approval_rate
        metric.outstanding_invoices_amount = outstanding_invoices_amount
        # billing_error_rate remains 0.0 for now unless we add an error log table
        
        await self.db.commit()
        await self.db.refresh(metric)
        return metric
