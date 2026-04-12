const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9500';
const API_URL = BASE_URL.includes('/api/v1') ? BASE_URL : `${BASE_URL}/api/v1`;

const originalFetch = globalThis.fetch;
const fetch = async (url: RequestInfo | URL, init?: RequestInit) => {
  return originalFetch(url, {
    ...init,
    headers: {
      ...init?.headers,
      "ngrok-skip-browser-warning": "69420",
    },
  });
};

export const portalApi = {
  // Accounts
  login: async (email: string, pass: string) => {
    const res = await fetch(`${API_URL}/portal/accounts/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass }),
    });
    return res.json();
  },
  searchPatient: async (query: string) => {
    const res = await fetch(`${API_URL}/portal/accounts/search?query=${query}`);
    return res.json();
  },

  // Medical Records
  getPatientInfo: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/accounts/profile?patient_id=${patientId}`);
    return res.json();
  },
  getLabResults: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/medical-records/lab-results?patient_id=${patientId}`);
    return res.json();
  },
  getPrescriptions: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/medical-records/prescriptions?patient_id=${patientId}`);
    return res.json();
  },
  getEncounters: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/medical-records/encounters?patient_id=${patientId}`);
    return res.json();
  },

  // Appointments
  getDoctors: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/appointments/doctors?patient_id=${patientId}`);
    return res.json();
  },
  getDoctorSlots: async (doctorId: string, date: string) => {
    const res = await fetch(`${API_URL}/portal/appointments/slots?doctor_id=${doctorId}&date=${date}`);
    return res.json();
  },
  getMyAppointments: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/appointments/my?patient_id=${patientId}`);
    return res.json();
  },
  bookAppointment: async (bookingData: any) => {
    const params = new URLSearchParams({
      patient_id: bookingData.patient_id,
      doctor_id: bookingData.doctor_id,
      appointment_time: bookingData.appointment_time,
      type: bookingData.type || "in_person",
      reason: bookingData.reason || ""
    });
    if (bookingData.slot_id) params.append("slot_id", bookingData.slot_id);
    
    const res = await fetch(`${API_URL}/portal/appointments/book?${params.toString()}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to book appointment');
    }
    return res.json();
  },

  // Telemedicine
  getTelemedicineSessions: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/telemedicine/sessions?patient_id=${patientId}`);
    return res.json();
  },

  // Billing
  getInvoices: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/billing/invoices?patient_id=${patientId}`);
    return res.json();
  }
};

