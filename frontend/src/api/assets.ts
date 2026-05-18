
import apiClient from './client';
import type { AssetCreateRequest, AssetUpdateRequest } from '../types';

export const assetsApi = {
  list: (params: { type?: string; page?: number; page_size?: number; search?: string; enabled?: boolean }) =>
    apiClient.get('/assets', { params }),
  get: (id: string) => apiClient.get(`/assets/${id}`),
  create: (data: AssetCreateRequest) => apiClient.post('/assets', data),
  update: (id: string, data: AssetUpdateRequest) => apiClient.put(`/assets/${id}`, data),
  delete: (id: string) => apiClient.delete(`/assets/${id}`),
  test: (id: string) => apiClient.post(`/assets/${id}/test`),
  toggle: (id: string, enabled: boolean) => apiClient.post(`/assets/${id}/toggle`, { enabled }),
};
