import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, PlusCircle, BarChart3,
  FileText, Settings, LogOut, Activity, Clock,
  Radio
} from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard' },
  { icon: PlusCircle, label: 'New Survey', to: '/upload' },
  { icon: Clock, label: 'Temporal Intelligence', to: '/temporal' },
  { icon: Activity, label: 'Evaluation', to: '/evaluation' },
  { icon: FileText, label: 'Reports', to: '/reports' },
  { icon: Settings, label: 'Settings', to: '/settings' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 bg-navy-900 flex flex-col h-full text-white shrink-0">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-navy-700/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sonar-cyan/20 border border-sonar-cyan/40 flex items-center justify-center">
            <Radio className="w-5 h-5 text-sonar-cyan" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider text-white">SONAR-X</h1>
            <p className="text-xs text-slate-400 leading-tight">Marine Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      {navItems.map(({ icon: Icon, label, to }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-sonar-cyan/15 text-sonar-cyan border border-sonar-cyan/30'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{label}</span>
            </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      <div className="p-4 border-t border-navy-700/50">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-ocean-600 flex items-center justify-center text-xs font-bold">
            {user?.full_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-sm text-white truncate">{user?.full_name || user?.email}</p>
            <p className="text-xs text-slate-400">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 text-sm transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  )
}
