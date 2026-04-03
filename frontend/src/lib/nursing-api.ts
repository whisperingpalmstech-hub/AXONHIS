import { api } from "./api";

export const nursingApi = {
  getCoversheet: async (admission_number: string) => {
    const { data } = await api.get(`/nursing/coversheet/${admission_number}`);
    return data;
  },

  logVitals: async (payload: any) => {
    const { data } = await api.post("/nursing/vitals", payload);
    return data;
  },

  addClinicalNote: async (payload: any) => {
    const { data } = await api.post("/nursing/notes", payload);
    return data;
  }
};
