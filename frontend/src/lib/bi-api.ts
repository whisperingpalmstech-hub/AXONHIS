import { api } from "./api";

export interface AnalyticsBaseStats {
  total_patients_registered_today: number;
  total_opd_visits_today: number;
  patients_waiting: number;
  avg_waiting_time_mins: number;
  patients_in_consultation: number;
}

export interface AnalyticsDoctorProductivity {
  doctor_name: string;
  department: string;
  patients_seen: number;
  avg_consult_time_mins: number;
  revenue_generated: number;
}

export interface AnalyticsRevenueSplit {
  department: string;
  net_revenue: number;
}

export interface AnalyticsClinicalDisease {
  disease_name: string;
  incidence_count: number;
}

export interface AnalyticsCrowdPrediction {
  target_date: string;
  department: string;
  predicted_footfall: number;
  peak_hours_expected: string;
  is_anomaly_alert: boolean;
}

export interface ManagementIntelligenceDashboard {
  referral_sources: Record<string, number>;
  retention_rate_pct: number;
}

class HospitalIntelligenceApi {
  async getRealTimeDashboard(): Promise<AnalyticsBaseStats> {
    const response = await api.get<AnalyticsBaseStats>("/bi-intelligence/dashboard/realtime");
    return response;
  }

  async getDoctorProductivity(): Promise<AnalyticsDoctorProductivity[]> {
    const response = await api.get<AnalyticsDoctorProductivity[]>("/bi-intelligence/analytics/productivity");
    return response;
  }

  async getFinancialAnalytics(): Promise<AnalyticsRevenueSplit[]> {
    const response = await api.get<AnalyticsRevenueSplit[]>("/bi-intelligence/analytics/financial");
    return response;
  }

  async getClinicalStatistics(): Promise<AnalyticsClinicalDisease[]> {
    const response = await api.get<AnalyticsClinicalDisease[]>("/bi-intelligence/analytics/clinical");
    return response;
  }

  async getCrowdForecasting(targetDate: string): Promise<AnalyticsCrowdPrediction[]> {
    const response = await api.get<AnalyticsCrowdPrediction[]>(`/bi-intelligence/forecasting/crowd/${targetDate}`);
    return response;
  }

  async getManagementIntelligence(): Promise<ManagementIntelligenceDashboard> {
    const response = await api.get<ManagementIntelligenceDashboard>("/bi-intelligence/dashboard/management");
    return response;
  }

  async generateExportReport(req: any): Promise<any> {
    const response = await api.post<any>("/bi-intelligence/reports/export", req);
    return response;
  }
}

export const biApi = new HospitalIntelligenceApi();
