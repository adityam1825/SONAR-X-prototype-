/**
 * SONAR-X Authentication Hook
 */

import { create } from 'zustand'
import { authAPI } from '../services/api'
import type { User } from '../types'

interface AuthStore {
  user: User | null
  access: string | null
  refresh: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loadFromStorage: () => void
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  access: null,
  refresh: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  loadFromStorage: () => {
    const access = localStorage.getItem('sonarx_access')
    const refresh = localStorage.getItem('sonarx_refresh')
    const userStr = localStorage.getItem('sonarx_user')
    if (access && userStr) {
      set({
        access,
        refresh,
        user: JSON.parse(userStr),
        isAuthenticated: true,
      })
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const resp = await authAPI.login(email, password)
      const { access, refresh, user } = resp.data as {
        access: string
        refresh: string
        user: User
      }
      localStorage.setItem('sonarx_access', access)
      localStorage.setItem('sonarx_refresh', refresh)
      localStorage.setItem('sonarx_user', JSON.stringify(user))
      set({ access, refresh, user, isAuthenticated: true, isLoading: false, error: null })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Login failed. Please check your credentials.'
      set({ isLoading: false, error: msg })
      throw err
    }
  },

  logout: async () => {
    const { refresh } = get()
    try {
      if (refresh) await authAPI.logout(refresh)
    } catch {}
    localStorage.removeItem('sonarx_access')
    localStorage.removeItem('sonarx_refresh')
    localStorage.removeItem('sonarx_user')
    set({ user: null, access: null, refresh: null, isAuthenticated: false })
  },
}))

// Convenient hook
export function useAuth() {
  return useAuthStore()
}
