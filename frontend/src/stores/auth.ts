import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import type { Session, User as SupabaseUser } from '@supabase/supabase-js'

interface AuthState {
  user: User | null
  session: Session | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (session: Session, user: User) => void
  logout: () => void
  setLoading: (loading: boolean) => void
  setSession: (session: Session | null) => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      session: null,
      isAuthenticated: false,
      isLoading: true,

      login: (session: Session, user: User) => {
        set({
          session,
          user,
          isAuthenticated: true,
          isLoading: false,
        })
      },

      logout: async () => {
        await supabase.auth.signOut()
        set({
          session: null,
          user: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      setSession: (session: Session | null) => {
        set({
          session,
          isAuthenticated: !!session,
        })
      },

      setUser: (user: User | null) => {
        set({ user })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
