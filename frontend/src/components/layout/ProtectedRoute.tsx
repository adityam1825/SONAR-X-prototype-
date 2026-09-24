import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../hooks/useAuth'

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}
