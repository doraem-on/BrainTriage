import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bt_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const loginRequest = (username, password) =>
  api.post('/api/auth/login', { username, password }).then(r => r.data)
export const me = () => api.get('/api/auth/me').then(r => r.data)

export const getSchema = () => api.get('/api/meta/schema').then(r => r.data)
export const getModelCard = () => api.get('/api/meta/model-card').then(r => r.data)

export const listPatients = () => api.get('/api/patients').then(r => r.data)
export const getPatient = (id) => api.get(`/api/patients/${id}`).then(r => r.data)
export const createPatient = (payload) => api.post('/api/patients', payload).then(r => r.data)
export const submitStage = (id, stage, data) =>
  api.post(`/api/patients/${id}/stage`, { stage, data }).then(r => r.data)
export const getHistory = (id) => api.get(`/api/patients/${id}/history`).then(r => r.data)
export const deletePatient = (id) => api.delete(`/api/patients/${id}`).then(r => r.data)
export const simulatePatient = (id, overrides) =>
  api.post(`/api/patients/${id}/simulate`, overrides).then(r => r.data)

export const getQueue = () => api.get('/api/queue').then(r => r.data)
export const getQueueStats = () => api.get('/api/queue/stats').then(r => r.data)
export const getOptimize = (slots) => api.get('/api/queue/optimize', { params: slots }).then(r => r.data)

// Plain <a href> links can't carry the Authorization header, so the PDF is
// fetched as a blob (picks up the interceptor above) and downloaded via a
// throwaway object URL instead of linking straight to the API route.
export const downloadReport = async (id, filename) => {
  const resp = await api.get(`/api/patients/${id}/report`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || `braintriage_${id}.pdf`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export const geocode = (q) => api.get('/api/locations/geocode', { params: { q } }).then(r => r.data)
export const getNearbyHospitals = (lat, lon, radius_km) =>
  api.get('/api/locations/hospitals', { params: { lat, lon, radius_km } }).then(r => r.data)
export const getEmergencyNumbers = () => api.get('/api/locations/emergency-numbers').then(r => r.data)

export const getAssistantStatus = () => api.get('/api/assistant/status').then(r => r.data)

export const API_BASE_URL = api.defaults.baseURL

export default api
