
import apiClient from './client';

export const dashboardApi = {
  userStats: () => apiClient.get('/user/dashboard/stats'),
  adminStats: () => apiClient.get('/admin/dashboard/stats'),
};
