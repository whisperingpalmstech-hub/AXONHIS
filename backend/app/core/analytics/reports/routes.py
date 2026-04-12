import io
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.dependencies import CurrentUser, DBSession

from app.core.analytics.clinical_metrics.services import ClinicalMetricService
from app.core.analytics.financial_metrics.services import FinancialMetricService
from app.core.analytics.operational_metrics.services import OperationalMetricService

router = APIRouter(prefix="/reports", tags=["Analytics - Reports"])

@router.get("/export")
async def export_report(
    db: DBSession,
    current_user: CurrentUser,
    report_type: str = Query(..., description="Type of report: 'clinical', 'financial', 'operational'"),
    days: int = Query(30, description="Number of days to export")
):
    """
    Export analytics data as CSV.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "clinical":
        svc = ClinicalMetricService(db)
        metrics = await svc.get_recent_metrics(days)
        writer.writerow(["Date", "Admissions", "Readmission Rate (%)", "Avg LOS (hrs)", "Avg Lab Turnaround (hrs)", "Critical Alerts"])
        for m in metrics:
            writer.writerow([
                m.metric_date,
                m.admissions_count,
                m.readmission_rate,
                m.average_los_hours,
                m.avg_lab_turnaround_hours,
                m.critical_alerts_count
            ])
        filename = f"clinical_report_{datetime.now().strftime('%Y%m%d')}.csv"

    elif report_type == "financial":
        svc = FinancialMetricService(db)
        metrics = await svc.get_recent_metrics(days)
        writer.writerow(["Date", "Daily Revenue", "Outstanding Invoices", "Claims Completed", "Claims Rejected"])
        for m in metrics:
            writer.writerow([
                m.metric_date,
                m.daily_revenue,
                m.outstanding_invoices_amount,
                m.claims_completed,
                m.claims_rejected
            ])
        filename = f"financial_report_{datetime.now().strftime('%Y%m%d')}.csv"

    elif report_type == "operational":
        svc = OperationalMetricService(db)
        metrics = await svc.get_recent_metrics(days)
        writer.writerow(["Date", "Bed Occupancy (%)", "Staff On Duty", "Patient Throughput", "Avg Wait Time (mins)", "Resource Utilization (%)"])
        for m in metrics:
            writer.writerow([
                m.metric_date,
                m.bed_occupancy_rate,
                m.staff_on_duty,
                m.patient_throughput,
                m.avg_wait_time_minutes,
                m.resource_utilization_rate
            ])
        filename = f"operational_report_{datetime.now().strftime('%Y%m%d')}.csv"

    else:
        raise HTTPException(status_code=400, detail="Invalid report type specified. Must be one of 'clinical', 'financial', 'operational'.")

    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
