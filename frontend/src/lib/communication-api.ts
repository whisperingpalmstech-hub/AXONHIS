import { api } from './api';

export const communicationApi = {
  // Messages
  sendMessage: async (data: { receiver_id: string; message_content: string; message_type?: string }) => {
    return await api.post('/communication/message/', data);
  },
  getMessages: async (otherUserId: string) => {
    return await api.get(`/communication/message/${otherUserId}`);
  },
  markMessageRead: async (messageId: string) => {
    return await api.put(`/communication/message/${messageId}/read`);
  },

  // Channels
  createChannel: async (data: { channel_name: string; department?: string }) => {
    return await api.post('/communication/channel/', data);
  },
  getChannels: async () => {
    return await api.get('/communication/channel/');
  },
  sendChannelMessage: async (data: { channel_id: string; message_content: string }) => {
    return await api.post('/communication/channel/message', data);
  },
  getChannelMessages: async (channelId: string) => {
    return await api.get(`/communication/channel/${channelId}/messages`);
  },

  // Alerts
  createAlert: async (data: { patient_id: string; alert_type: string; severity: string; message: string }) => {
    return await api.post('/communication/alert/', data);
  },
  getAlerts: async () => {
    return await api.get('/communication/alert/');
  },
  acknowledgeAlert: async (alertId: string) => {
    return await api.put(`/communication/alert/${alertId}/acknowledge`);
  },

  // Notifications
  getNotifications: async () => {
    return await api.get('/communication/notification/');
  },
  markNotificationRead: async (notificationId: string) => {
    return await api.put(`/communication/notification/${notificationId}/read`);
  },

  // Escalations
  createEscalation: async (data: { task_id: string; escalated_to: string; reason: string }) => {
    return await api.post('/communication/escalation/', data);
  },
  getEscalations: async () => {
    return await api.get('/communication/escalation/');
  },
  
  // Auth/Users (for dropdowns)
  getUsers: async (skip = 0, limit = 100) => {
    return await api.get(`/auth/users?skip=${skip}&limit=${limit}`);
  },

  // Patients (for dropdowns)
  getPatients: async (skip = 0, limit = 100) => {
    return await api.get(`/patients/?skip=${skip}&limit=${limit}`);
  }
};
