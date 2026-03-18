const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9500/api/v1';

export const portalApi = {
  // Accounts
  login: async (email, password) => {
    const res = await fetch(`${API_URL}/portal/accounts/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return res.json();
  },

  // Medical Records
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
  getDoctors: async () => {
    const res = await fetch(`${API_URL}/portal/appointments/doctors`);
    return res.json();
  },
  getMyAppointments: async (patientId: string) => {
    const res = await fetch(`${API_URL}/portal/appointments/my?patient_id=${patientId}`);
    return res.json();
  },
  bookAppointment: async (bookingData: any) => {
     const res = await fetch(`${API_URL}/portal/appointments/book`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    });
    return res.json();
  }
};
