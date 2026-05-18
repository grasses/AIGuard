
import apiClient from './client';
import type { TrafficConfigCreateRequest } from '../types';

export const trafficApi = {
  list: (params: any) => apiClient.get('/traffic-configs', { params }),
  get: (id: string) => apiClient.get(`/traffic-configs/${id}`),
  create: (data: TrafficConfigCreateRequest) => apiClient.post('/traffic-configs', data),
  update: (id: string, data: any) => apiClient.put(`/traffic-configs/${id}`, data),
  delete: (id: string) => apiClient.delete(`/traffic-configs/${id}`),
};
