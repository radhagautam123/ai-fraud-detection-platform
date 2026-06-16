import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export function setAuthToken(token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export function clearAuthToken() {
  delete api.defaults.headers.common['Authorization']
}

// Restore token from storage on load
const savedToken = localStorage.getItem('token')
if (savedToken) {
  setAuthToken(savedToken)
}

// Metrics & Monitoring
export const getMetrics = () => api.get('/metrics').then(r => r.data)
export const getSystemHealth = () => api.get('/system-health').then(r => r.data)
export const getSystemMetrics = () => api.get('/system-metrics').then(r => r.data)

// Auth
export const loginUser = (username, password) =>
  api.post('/auth/login', { username, password }).then(r => r.data)

export const registerUser = (data) =>
  api.post('/auth/register', data).then(r => r.data)

export const getMe = () => api.get('/users/me').then(r => r.data)

export const getUsers = () => api.get('/users').then(r => r.data)

// Alerts
export const getAlerts = (params = {}) =>
  api.get('/alerts', { params }).then(r => r.data)

export const getAlertDetail = (id) =>
  api.get(`/alerts/${id}`).then(r => r.data)

// Case Management
export const assignAlert = (id, assigned_to) =>
  api.patch(`/alerts/${id}/assign`, { assigned_to }).then(r => r.data)

export const updateAlertStatus = (id, status) =>
  api.patch(`/alerts/${id}/status`, { status }).then(r => r.data)

export const updateAlertNotes = (id, case_notes) =>
  api.patch(`/alerts/${id}/notes`, { case_notes }).then(r => r.data)

export const resolveAlert = (id, resolution) =>
  api.patch(`/alerts/${id}/resolve`, { status: resolution }).then(r => r.data)

// Transactions
export const getTransactions = (params = {}) =>
  api.get('/transactions', { params }).then(r => r.data)

// Audit Logs
export const getAuditLogs = (params = {}) =>
  api.get('/audit-logs', { params }).then(r => r.data)

// Charts
export const getRiskDistribution = () =>
  api.get('/risk-distribution').then(r => r.data)

export const getModelInfo = () =>
  api.get('/model-info').then(r => r.data)

export const getFraudTrend = (period = 'day', limit = 30) =>
  api.get('/fraud-trend', { params: { period, limit } }).then(r => r.data)

export const getTopMerchants = (limit = 10) =>
  api.get('/top-merchants', { params: { limit } }).then(r => r.data)

export const getRiskScoreDistribution = () =>
  api.get('/risk-score-distribution').then(r => r.data)
