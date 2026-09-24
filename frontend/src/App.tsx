import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './hooks/useAuth'
import AppLayout from './layouts/AppLayout'
import ProtectedRoute from './components/layout/ProtectedRoute'

// Pages
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadOnlyPage from './pages/UploadOnlyPage'
import AutoProcessingPage from './pages/AutoProcessingPage'
import NewSurveyPage from './pages/surveys/NewSurveyPage'       // kept for advanced/admin use
import SurveyDetailPage from './pages/surveys/SurveyDetailPage'
import UploadPage from './pages/surveys/UploadPage'
import ValidationPage from './pages/surveys/ValidationPage'
import PreprocessingPage from './pages/surveys/PreprocessingPage'
import AnalysisPage from './pages/surveys/AnalysisPage'
import ResultsPage from './pages/surveys/ResultsPage'
import DetectionDetailPage from './pages/DetectionDetailPage'
import MapPage from './pages/surveys/MapPage'
import ExportPage from './pages/surveys/ExportPage'
import TemporalPage from './pages/surveys/TemporalPage'
import VerifyPage from './pages/detections/VerifyPage'
import EvaluationPage from './pages/EvaluationPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import TemporalIntelligencePage from './pages/TemporalIntelligencePage'

export default function App() {
  const { loadFromStorage } = useAuthStore()

  useEffect(() => {
    loadFromStorage()
  }, [])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      {/* Upload-only pages — full screen, no app chrome */}
      <Route element={<ProtectedRoute />}>
        {/* Primary user entry point: upload sonar data */}
        <Route path="/upload" element={<UploadOnlyPage />} />
        {/* Automatic processing progress screen */}
        <Route path="/processing" element={<AutoProcessingPage />} />
      </Route>

      {/* App shell routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Upload-only workflow: /surveys/new now redirects to /upload */}
          <Route path="/surveys/new" element={<Navigate to="/upload" replace />} />

          {/* Advanced survey creation (kept for demo/admin access) */}
          <Route path="/surveys/create-advanced" element={<NewSurveyPage />} />

          <Route path="/surveys/:id" element={<SurveyDetailPage />} />
          <Route path="/surveys/:id/upload" element={<UploadPage />} />
          <Route path="/surveys/:id/validation" element={<ValidationPage />} />
          <Route path="/surveys/:id/preprocessing" element={<PreprocessingPage />} />
          <Route path="/surveys/:id/analysis" element={<AnalysisPage />} />
          <Route path="/surveys/:id/results" element={<ResultsPage />} />
          <Route path="/surveys/:id/map" element={<MapPage />} />
          <Route path="/surveys/:id/export" element={<ExportPage />} />
          <Route path="/surveys/:id/temporal" element={<TemporalPage />} />
          <Route path="/detections/:id" element={<DetectionDetailPage />} />
          <Route path="/detections/:id/verify" element={<VerifyPage />} />
          <Route path="/temporal" element={<TemporalIntelligencePage />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
