
import { create } from 'zustand';
import { alertsApi } from '../api/alerts';

interface NotificationState {
  unreadCount: number;
  fetchUnreadCount: () => Promise<void>;
  setUnreadCount: (count: number) => void;
}

export const useNotificationStore = create<NotificationState>()((set) => ({
  unreadCount: 0,

  fetchUnreadCount: async () => {
    try {
      const res = await alertsApi.unreadCount();
      set({ unreadCount: res.data.data.count });
    } catch {
      // ignore
    }
  },

  setUnreadCount: (count) => set({ unreadCount: count }),
}));
