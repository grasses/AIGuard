
import apiClient from './client';

export const alertsApi = {
  listRules: (params: any) => apiClient.get('/alert-rules', { params }),
  createRule: (data: any) => apiClient.post('/alert-rules', data),
  getRule: (id: string) => apiClient.get(`/alert-rules/${id}`),
  updateRule: (id: string, data: any) => apiClient.put(`/alert-rules/${id}`, data),
  deleteRule: (id: string) => apiClient.delete(`/alert-rules/${id}`),
  listEvents: (params: any) => apiClient.get('/alerts', { params }),
  markAllRead: () => apiClient.post('/alerts/read-all'),
  unreadCount: () => apiClient.get('/alerts/unread-count'),
};
