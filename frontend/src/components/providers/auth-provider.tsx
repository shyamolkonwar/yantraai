"use client"

import { useEffect } from 'react'
import { useAuthStore } from '@/stores/auth'
import { supabase } from '@/lib/supabase'
import { authAPI } from '@/lib/api'

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { login, logout, setLoading, setSession, setUser } = useAuthStore()

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Get initial session
        const { data: { session }, error } = await supabase.auth.getSession()

        if (error) {
          console.error('Error getting session:', error)
          setLoading(false)
          return
        }

        if (session) {
          setSession(session)
          // Get user data from backend using Supabase session token
          try {
            const response = await authAPI.testToken()
            setUser(response.data)
          } catch (backendError) {
            console.error('Error getting user from backend:', backendError)
            // If backend fails, still set session but user will be null
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event, session)

        if (event === 'SIGNED_IN' && session) {
          setSession(session)
          try {
            // Get user data from backend
            const response = await authAPI.testToken()
            setUser(response.data)
          } catch (error) {
            console.error('Error getting user from backend:', error)
            // User signed in but backend user fetch failed
            setUser(null)
          }
        } else if (event === 'SIGNED_OUT') {
          setSession(null)
          setUser(null)
        }
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [setLoading, setSession, setUser])

  return <>{children}</>
}
