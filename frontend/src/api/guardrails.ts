
import apiClient from './client';
import type { GuardrailCreateRequest, GuardrailUpdateRequest } from '../types';

export const guardrailsApi = {
  list: (params: any) => apiClient.get('/guardrails', { params }),
  get: (id: string) => apiClient.get(`/guardrails/${id}`),
  create: (data: GuardrailCreateRequest) => apiClient.post('/guardrails', data),
  update: (id: string, data: GuardrailUpdateRequest) => apiClient.put(`/guardrails/${id}`, data),
  delete: (id: string) => apiClient.delete(`/guardrails/${id}`),
  test: (id: string, data: { messages: any[]; metadata?: any }) => apiClient.post(`/guardrails/${id}/test`, data),
  toggle: (id: string, enabled: boolean) => apiClient.post(`/guardrails/${id}/toggle`, { enabled }),
};
