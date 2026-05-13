import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';
import { authService } from '../services/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  checkAuth: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,

      setUser: (user) => set({ user, isAuthenticated: !!user }),

      checkAuth: async () => {
        set({ isLoading: true });
        try {
          const auth = await authService.isAuthenticated();
          if (auth) {
            const profile = await authService.getFullProfile();
            set({ user: profile, isAuthenticated: true, isLoading: false });
          } else {
            set({ user: null, isAuthenticated: false, isLoading: false });
          }
        } catch (err) {
          set({ error: (err as Error).message, isLoading: false });
        }
      },

      refreshProfile: async () => {
        try {
          const profile = await authService.getFullProfile();
          set({ user: profile });
        } catch (err) {
          console.error("Failed to refresh profile:", err);
        }
      },

      logout: async () => {
        await authService.logout();
        set({ user: null, isAuthenticated: false });
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
