import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export const getSchema = () => api.get('/api/meta/schema').then(r => r.data)
export const getModelCard = () => api.get('/api/meta/model-card').then(r => r.data)

export const listPatients = () => api.get('/api/patients').then(r => r.data)
export const getPatient = (id) => api.get(`/api/patients/${id}`).then(r => r.data)
export const createPatient = (payload) => api.post('/api/patients', payload).then(r => r.data)
export const submitStage = (id, stage, data) =>
  api.post(`/api/patients/${id}/stage`, { stage, data }).then(r => r.data)
export const getHistory = (id) => api.get(`/api/patients/${id}/history`).then(r => r.data)
export const deletePatient = (id) => api.delete(`/api/patients/${id}`).then(r => r.data)

export const getQueue = () => api.get('/api/queue').then(r => r.data)
export const getQueueStats = () => api.get('/api/queue/stats').then(r => r.data)

export const reportUrl = (id) => `${api.defaults.baseURL}/api/patients/${id}/report`

export default api
