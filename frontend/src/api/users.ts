
import apiClient from './client';

export const usersApi = {
  list: (params: any) => apiClient.get('/admin/users', { params }),
  get: (id: string) => apiClient.get(`/admin/users/${id}`),
  update: (id: string, data: any) => apiClient.put(`/admin/users/${id}`, data),
};
