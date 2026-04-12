export interface Site {
  id?: string;
  name: string;
  site_code: string;
  location_address?: string;
  timezone?: string;
  is_active?: boolean;
}

export interface Organization {
  id?: string;
  name: string;
  org_code: string;
  country?: string;
  contact_email?: string;
  is_active?: boolean;
  default_language?: string;
  sites?: Site[];
  global_settings?: any;
  admin_password?: string;
}

const BASE_URL = 'http://localhost:9500/api/v1/administration/tenants';

const getHeaders = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
};

export const tenantsApi = {
  getOrganizations: async (): Promise<Organization[]> => {
    const res = await fetch(`${BASE_URL}/organizations`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch orgs');
    return res.json();
  },
  
  createOrganization: async (data: any): Promise<Organization> => {
    const res = await fetch(`${BASE_URL}/organizations`, {
      method: "POST", headers: getHeaders(), body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to create org');
    return res.json();
  },

  addSite: async (orgId: string, data: any): Promise<Site> => {
    const res = await fetch(`${BASE_URL}/organizations/${orgId}/sites`, {
      method: "POST", headers: getHeaders(), body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to add site');
    return res.json();
  },

  toggleVoiceSettings: async (orgId: string, enable: boolean): Promise<any> => {
    const res = await fetch(`${BASE_URL}/organizations/${orgId}/voice?enable=${enable}`, {
      method: "POST", headers: getHeaders()
    });
    if (!res.ok) throw new Error('Failed to toggle voice');
    return res.json();
  },

  changeLanguage: async (orgId: string, lang: string): Promise<any> => {
    const res = await fetch(`${BASE_URL}/organizations/${orgId}/language?lang=${lang}`, {
      method: "POST", headers: getHeaders()
    });
    if (!res.ok) throw new Error('Failed to change language');
    return res.json();
  }
};
