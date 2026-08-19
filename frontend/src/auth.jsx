import { createContext, useContext, useEffect, useState } from 'react'
import { loginRequest, me } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('bt_token'))
  const [username, setUsername] = useState(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!token) { setChecking(false); return }
    me().then(u => { setUsername(u.username); setChecking(false) })
      .catch(() => { logout(); setChecking(false) })
  }, [token]) // eslint-disable-line react-hooks/exhaustive-deps

  const login = async (username, password) => {
    const { access_token } = await loginRequest(username, password)
    localStorage.setItem('bt_token', access_token)
    setToken(access_token)
  }

  const logout = () => {
    localStorage.removeItem('bt_token')
    setToken(null)
    setUsername(null)
  }

  return (
    <AuthContext.Provider value={{ token, username, checking, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
