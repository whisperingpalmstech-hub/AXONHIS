import { api } from "./api";

export const nursingApi = {
  getCoversheet: async (admission_number: string) => {
    const data = await api.get<any>(`/nursing/coversheet/${admission_number}`);
    return data;
  },

  logVitals: async (payload: any) => {
    const data = await api.post<any>("/nursing/vitals", payload);
    return data;
  },

  addClinicalNote: async (payload: any) => {
    const data = await api.post<any>("/nursing/notes", payload);
    return data;
  }
};
