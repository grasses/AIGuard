
import apiClient from './client';
import type { LoginRequest, RegisterRequest, User } from '../types';

export const authApi = {
  login: (data: LoginRequest) => apiClient.post('/auth/login', data),
  register: (data: RegisterRequest) => apiClient.post('/auth/register', data),
  refresh: (refreshToken: string) => apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  forgotPassword: (email: string) => apiClient.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, newPassword: string) => apiClient.post('/auth/reset-password', { token, new_password: newPassword }),
  getProfile: () => apiClient.get('/user/profile'),
  changePassword: (oldPassword: string, newPassword: string) => apiClient.post('/user/change-password', { old_password: oldPassword, new_password: newPassword }),
  listApiKeys: () => apiClient.get('/user/api-keys'),
  createApiKey: (name: string) => apiClient.post('/user/api-keys', { name }),
  deleteApiKey: (id: string) => apiClient.delete(`/user/api-keys/${id}`),
};
