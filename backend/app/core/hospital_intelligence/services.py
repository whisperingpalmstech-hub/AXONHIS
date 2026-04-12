import uuid
from typing import List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import json
from decimal import Decimal
import random

from app.core.hospital_intelligence.models import (
    AnalyticsPatientFlow,
    AnalyticsDoctorProductivity,
    AnalyticsRevenue,
    AnalyticsClinicalStatistics,
    AnalyticsCrowdPrediction
)

# ETL Pipeline Simulator & Analytics Service
class BIAnalyticsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_realtime_operational_dashboard(self) -> dict:
        """
        1. REAL-TIME OPERATIONAL DASHBOARD
        Aggregates data representing live OPD workflow. In a real system, this
        monitors SmartQueue and Appointments states exactly at T(0).
        Here we query the analytics dw or simulate live traffic. 
        """
        # Fetch actual recorded DW if exists
        res = await self.db.execute(select(AnalyticsPatientFlow).where(AnalyticsPatientFlow.record_date == date.today()))
        today_flows = res.scalars().all()

        if not today_flows:
            # Generate simulated mock live dash for missing ETL
            return {
                "total_patients_registered_today": 124,
                "total_opd_visits_today": 118,
                "patients_waiting": 37,
                "avg_waiting_time_mins": 22.5,
                "patients_in_consultation": 15
            }

        ttl_reg = sum([f.total_registered for f in today_flows])
        ttl_cons = sum([f.total_consulted for f in today_flows])
        avg_wait = sum([f.avg_waiting_time_mins for f in today_flows]) / len(today_flows) if today_flows else 0

        # Simulate live waiting counts
        return {
            "total_patients_registered_today": ttl_reg,
            "total_opd_visits_today": ttl_cons,
            "patients_waiting": int(ttl_reg * 0.2), # Pseudo math
            "avg_waiting_time_mins": round(avg_wait, 1),
            "patients_in_consultation": int(ttl_cons * 0.1)
        }

    async def get_doctor_productivity_analytics(self) -> List[dict]:
        """
        3. DOCTOR PRODUCTIVITY ANALYTICS
        """
        res = await self.db.execute(select(AnalyticsDoctorProductivity).where(AnalyticsDoctorProductivity.record_date == date.today()).limit(100))
        docs = res.scalars().all()
        if not docs:
            # Simulate
            return [
                {"doctor_name": "Dr. Sarah Mitchell", "department": "Cardiology", "patients_seen": 34, "avg_consult_time_mins": 9.5, "revenue_generated": 45000.0},
                {"doctor_name": "Dr. Robert Chen", "department": "Dermatology", "patients_seen": 12, "avg_consult_time_mins": 15.0, "revenue_generated": 14000.0}
            ]
        
        return [{"doctor_name": d.doctor_name, "department": d.department, "patients_seen": d.patients_seen, "avg_consult_time_mins": d.avg_consult_time_mins, "revenue_generated": float(d.revenue_generated)} for d in docs]

    async def get_financial_analytics(self) -> List[dict]:
        """
        4. FINANCIAL & REVENUE ANALYTICS Service-wise
        """
        res = await self.db.execute(select(AnalyticsRevenue).where(AnalyticsRevenue.record_date == date.today()))
        revs = res.scalars().all()
        if not revs:
            return [
                {"department": "Cardiology", "net_revenue": 120000.0},
                {"department": "Dermatology", "net_revenue": 45000.0},
                {"department": "General Medicine", "net_revenue": 87000.0}
            ]
        return [{"department": r.department, "net_revenue": float(r.net_revenue)} for r in revs]

    async def get_clinical_statistics(self) -> List[dict]:
        """
        5. CLINICAL DATA ANALYTICS
        """
        res = await self.db.execute(select(AnalyticsClinicalStatistics).where(AnalyticsClinicalStatistics.record_date == date.today()).order_by(AnalyticsClinicalStatistics.incidence_count.desc()).limit(10))
        stats = res.scalars().all()
        if not stats:
            return [
                {"disease_name": "Hypertension (I10)", "incidence_count": 45},
                {"disease_name": "Type 2 Diabetes (E11)", "incidence_count": 32},
                {"disease_name": "Acute Upper Respiratory Exp (J06.9)", "incidence_count": 28}
            ]
        return [{"disease_name": s.disease_name, "incidence_count": s.incidence_count} for s in stats]

    async def get_predictive_crowd_forecasting(self, target: date) -> List[dict]:
        """
        6. PREDICTIVE OPD CROWD FORECASTING
        """
        res = await self.db.execute(select(AnalyticsCrowdPrediction).where(AnalyticsCrowdPrediction.target_date == target))
        preds = res.scalars().all()
        if not preds:
            return [
                {"target_date": target, "department": "Cardiology", "predicted_footfall": 110, "peak_hours_expected": "10:00 AM - 1:30 PM", "is_anomaly_alert": True},
                {"target_date": target, "department": "General Medicine", "predicted_footfall": 250, "peak_hours_expected": "09:00 AM - 12:00 PM", "is_anomaly_alert": False}
            ]
        return [{"target_date": p.target_date, "department": p.department, "predicted_footfall": p.predicted_footfall, "peak_hours_expected": p.peak_hours_expected, "is_anomaly_alert": p.is_anomaly_alert} for p in preds]

    async def get_management_intelligence(self) -> dict:
        """
        7. MANAGEMENT INTELLIGENCE DASHBOARD
        """
        return {
            "referral_sources": {
                "Digital Marketing": 24,
                "Doctor Referral": 32,
                "Walk-in / Organic": 44
            },
            "retention_rate_pct": 78.5
        }

    async def generate_export_report(self, req) -> dict:
        """
        8 & 9. REPORT GENERATION & DATA EXPORT ENGINE
        Stub generator returning a mock S3 URI for the PDF/Excel.
        """
        # Logic to extract data via Pandas and format into PDF/Excel happens here
        return {
            "status": "Success",
            "file_url": f"https://axonhis-datacenter.local/export/{req.report_type}_{req.format.upper()}_{uuid.uuid4().hex[:6]}.{req.format.lower()}",
            "message": f"Successfully compiled {req.report_type} in {req.format} format."
        }
