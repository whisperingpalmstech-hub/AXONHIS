from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from app.database import get_db
from app.core.hospital_intelligence.schemas import (
    AnalyticsBaseStatsOut,
    AnalyticsDoctorProductivityOut,
    AnalyticsRevenueSplitOut,
    AnalyticsClinicalDiseaseOut,
    AnalyticsCrowdPredictionOut,
    ManagementIntelligenceDashboardOut,
    ExportFormatRequest
)
from app.core.hospital_intelligence.services import BIAnalyticsEngine

router = APIRouter(prefix="/bi-intelligence", tags=["Hospital Intelligence & Analytics Engine"])

@router.get("/dashboard/realtime", response_model=AnalyticsBaseStatsOut)
async def realtime_operational_dashboard(db: AsyncSession = Depends(get_db)):
    """1. REAL-TIME OPERATIONAL DASHBOARD"""
    engine = BIAnalyticsEngine(db)
    return await engine.get_realtime_operational_dashboard()

@router.get("/analytics/productivity", response_model=List[AnalyticsDoctorProductivityOut])
async def doctor_productivity(db: AsyncSession = Depends(get_db)):
    """3. DOCTOR PRODUCTIVITY ANALYTICS"""
    engine = BIAnalyticsEngine(db)
    return await engine.get_doctor_productivity_analytics()

@router.get("/analytics/financial", response_model=List[AnalyticsRevenueSplitOut])
async def financial_revenue(db: AsyncSession = Depends(get_db)):
    """4. FINANCIAL & REVENUE ANALYTICS"""
    engine = BIAnalyticsEngine(db)
    return await engine.get_financial_analytics()

@router.get("/analytics/clinical", response_model=List[AnalyticsClinicalDiseaseOut])
async def clinical_data(db: AsyncSession = Depends(get_db)):
    """5. CLINICAL DATA ANALYTICS"""
    engine = BIAnalyticsEngine(db)
    return await engine.get_clinical_statistics()

@router.get("/forecasting/crowd/{target_date}", response_model=List[AnalyticsCrowdPredictionOut])
async def predictive_crowd(target_date: date, db: AsyncSession = Depends(get_db)):
    """6. PREDICTIVE OPD CROWD FORECASTING"""
    engine = BIAnalyticsEngine(db)
    return await engine.get_predictive_crowd_forecasting(target_date)

@router.get("/dashboard/management", response_model=ManagementIntelligenceDashboardOut)
async def management_intelligence(db: AsyncSession = Depends(get_db)):
    """7. MANAGEMENT INTELLIGENCE DASHBOARD"""
    engine = BIAnalyticsEngine(db)
    return await engine.get_management_intelligence()

@router.post("/reports/export")
async def generate_export(req: ExportFormatRequest, db: AsyncSession = Depends(get_db)):
    """8. REPORT GENERATION SYSTEM & 9. DATA EXPORT & AUTOMATION ENGINE"""
    engine = BIAnalyticsEngine(db)
    return await engine.generate_export_report(req)
