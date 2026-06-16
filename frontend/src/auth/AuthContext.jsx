import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api, setAuthToken, clearAuthToken } from '../api/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setAuthToken(token)
      api.get('/users/me')
        .then((res) => setUser(res.data))
        .catch(() => {
          clearAuthToken()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (username, password) => {
    const res = await api.post('/auth/login', { username, password })
    const { access_token, user: userData } = res.data
    localStorage.setItem('token', access_token)
    setAuthToken(access_token)
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(() => {
    clearAuthToken()
    localStorage.removeItem('token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
