
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setAccessToken: (token: string) => void;
  updateBalance: (balance: number) => void;
  logout: () => void;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),

      setAccessToken: (accessToken) => set({ accessToken }),

      updateBalance: (balance) => {
        const user = get().user;
        if (user) set({ user: { ...user, balance } });
      },

      logout: () => set({ user: null, accessToken: null, refreshToken: null }),

      isAdmin: () => {
        const role = get().user?.role;
        return role === 'admin' || role === 'super_admin';
      },

      isSuperAdmin: () => get().user?.role === 'super_admin',
    }),
    { name: 'ai-firewall-auth' }
  )
);
