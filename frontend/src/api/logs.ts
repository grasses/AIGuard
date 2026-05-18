
import apiClient from './client';

export const logsApi = {
  list: (params: any) => apiClient.get('/logs', { params }),
  getDetail: (id: string) => apiClient.get(`/logs/${id}`),
};
