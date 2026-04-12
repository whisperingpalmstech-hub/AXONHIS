import { api } from "./api";

// --- TYPES ---
export interface HistoSlide {
  id: string; slide_label: string; staining_type: string; microscopic_diagnosis?: string; microscopic_images: string[]; prepared_at: string;
}
export interface HistoBlock {
  id: string; block_label: string; embedding_status: string; slides: HistoSlide[];
}
export interface HistoSpecimen {
  id: string; sample_id: string; patient_uhid: string; patient_name: string; current_stage: string; macroscopic_notes?: string; 
  is_sensitive: boolean; requires_counseling: boolean; counseling_status: string; is_oncology: boolean; created_at: string; blocks: HistoBlock[];
}

export interface AntiSensitivity {
  id: string; antibiotic_name: string; mic_value?: number; susceptibility: string;
}
export interface MicroCulture {
  id: string; sample_id: string; patient_uhid: string; source_department?: string; incubation_type?: string; 
  growth_findings?: string; organism_identified?: string; is_infection_control_screen: boolean; sensitivities: AntiSensitivity[];
}

export interface CSSDTest {
  id: string; test_sample_id: string; control_sample_id: string; sterilization_validated: boolean; 
  growth_in_test_sample: boolean; growth_in_control_sample: boolean; tested_at: string;
}
export interface BloodBankUnit {
  id: string; unit_id: string; blood_group: string; collection_date: string; expiry_date: string; component_type: string; status: string;
}

// --- API SDK ---
const BASE = "/advanced";

export const advancedLabApi = {
  // Histopathology
  getSpecimens: () => api.get<HistoSpecimen[]>(`${BASE}/histo/specimens`),
  advanceSpecimen: (id: string, new_stage: string, notes?: string) => api.put<HistoSpecimen>(`${BASE}/histo/specimens/${id}/advance`, { new_stage, macroscopic_notes: notes }),
  addSlideImage: (slide_id: string, image_url: string, diagnosis?: string) => api.post<HistoSlide>(`${BASE}/histo/slides/${slide_id}/images`, { slide_id, image_url, diagnosis }),

  // Microbiology
  getCultures: () => api.get<MicroCulture[]>(`${BASE}/micro/cultures`),
  recordGrowth: (id: string, findings: string, organism?: string) => api.put<MicroCulture>(`${BASE}/micro/cultures/${id}/growth`, { growth_findings: findings, organism_identified: organism }),
  addSensitivity: (id: string, abx: string, mic: number, sus: string) => api.post<AntiSensitivity>(`${BASE}/micro/cultures/${id}/sensitivities`, { antibiotic_name: abx, mic_value: mic, susceptibility: sus }),

  // CSSD
  getCSSDTests: () => api.get<CSSDTest[]>(`${BASE}/cssd/tests`),
  registerCSSD: (test_id: string, control_id: string) => api.post<CSSDTest>(`${BASE}/cssd/tests`, { test_sample_id: test_id, control_sample_id: control_id }),
  concludeCSSD: (id: string, growth_test: boolean, growth_control: boolean, dept: string) => api.put<CSSDTest>(`${BASE}/cssd/tests/${id}/conclude`, { growth_in_test_sample: growth_test, growth_in_control_sample: growth_control, report_sent_to: dept }),

  // Blood Bank
  getBloodBank: () => api.get<BloodBankUnit[]>(`${BASE}/blood-bank/inventory`),
  registerBloodUnit: (data: any) => api.post<BloodBankUnit>(`${BASE}/blood-bank/inventory`, data),
};
