/**
 * SONAR-X API Service
 * Axios client with JWT interceptors
 */

import axios, { AxiosError } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach JWT
api.interceptors.request.use(
  (config) => {
    const access = localStorage.getItem('sonarx_access')
    if (access) {
      config.headers.Authorization = `Bearer ${access}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor — handle 401, refresh token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refresh = localStorage.getItem('sonarx_refresh')
      if (refresh) {
        try {
          const resp = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh })
          const newAccess = (resp.data as { access: string }).access
          localStorage.setItem('sonarx_access', newAccess)
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccess}`
          }
          return api(originalRequest)
        } catch {
          localStorage.removeItem('sonarx_access')
          localStorage.removeItem('sonarx_refresh')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

// ── Auth ──────────────────────────────────────────────────────────

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login/', { email, password }),
  me: () => api.get('/auth/me/'),
  logout: (refresh: string) =>
    api.post('/auth/logout/', { refresh }),
}

// ── Surveys ───────────────────────────────────────────────────────

export const surveysAPI = {
  list: () => api.get('/surveys/'),
  get: (id: string) => api.get(`/surveys/${id}/`),
  create: (data: object) => api.post('/surveys/', data),
  stats: () => api.get('/surveys/stats/'),
  demo: () => api.get('/surveys/demo/'),
  analyze: (id: string) => api.post(`/surveys/${id}/analyze/`),
  followUp: (id: string, data: object) => api.post(`/surveys/${id}/follow_up/`, data),
  /** Upload-only ingest: accepts a file (or files), returns full analysis results */
  ingest: (formData: FormData, onProgress?: (pct: number) => void) =>
    api.post('/surveys/ingest/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
        ? (e) => {
            if (e.total) onProgress(Math.round((e.loaded * 100) / e.total))
          }
        : undefined,
    }),
}

// ── Sonar Files ───────────────────────────────────────────────────

export const sonarAPI = {
  upload: (surveyId: string, formData: FormData) =>
    api.post(`/files/${surveyId}/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  validate: (fileId: string) => api.post(`/files/${fileId}/validate/`),
  preprocess: (fileId: string, params?: object) =>
    api.post(`/files/${fileId}/preprocess/`, params || {}),
  processingLog: (fileId: string) => api.get(`/files/${fileId}/processing-log/`),
}

// ── Detections ────────────────────────────────────────────────────

export const detectionsAPI = {
  list: (params?: object) => api.get('/detections/', { params }),
  get: (id: string) => api.get(`/detections/${id}/`),
  hazard: (id: string) => api.get(`/detections/${id}/hazard/`),
  verify: (id: string, data: object) => api.post(`/detections/${id}/verify/`, data),
  history: (id: string) => api.get(`/detections/${id}/history/`),
  temporalAnalysis: (id: string) => api.get(`/detections/${id}/temporal_analysis/`),
  // Debris objects
  debrisList: () => api.get('/detections/debris/'),
  debrisGet: (uid: string) => api.get(`/detections/debris/${uid}/`),
  debrisVerifyTemporal: (uid: string, data: object) =>
    api.post(`/detections/debris/${uid}/verify_temporal/`, data),
}

// ── Exports ───────────────────────────────────────────────────────

export const exportsAPI = {
  geojson: (surveyId: string) =>
    api.get(`/exports/surveys/${surveyId}/geojson/`, { responseType: 'blob' }),
  kml: (surveyId: string) =>
    api.get(`/exports/surveys/${surveyId}/kml/`, { responseType: 'blob' }),
  csv: (surveyId: string) =>
    api.get(`/exports/surveys/${surveyId}/csv/`, { responseType: 'blob' }),
  summary: (surveyId: string) =>
    api.get(`/exports/surveys/${surveyId}/summary/`),
}

// ── Reports ───────────────────────────────────────────────────────

export const reportsAPI = {
  generateSurvey: (surveyId: string) =>
    api.post(`/reports/surveys/${surveyId}/`),
  generateTemporal: (debrisUid: string) =>
    api.post(`/reports/temporal/${debrisUid}/`),
  download: (reportId: string) =>
    api.get(`/reports/download/${reportId}/`, { responseType: 'blob' }),
}

// ── Temporal ──────────────────────────────────────────────────────

export const temporalAPI = {
  overview: () => api.get('/temporal/'),
  detail: (debrisUid: string) => api.get(`/temporal/${debrisUid}/`),
}

// ── Evaluation ────────────────────────────────────────────────────

export const evaluationAPI = {
  runs: () => api.get('/evaluation/runs/'),
  latest: () => api.get('/evaluation/runs/latest/'),
}

export default api

// ── Download helper ───────────────────────────────────────────────

export function downloadBlob(data: Blob, filename: string) {
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
