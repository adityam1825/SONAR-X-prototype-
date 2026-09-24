import { Bell } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

export default function TopBar() {
  const { user } = useAuth()

  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded">
          v0.1.0-prototype
        </span>
        {user?.role === 'DEMO' && (
          <span className="text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">
            DEMO MODE
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
          <span className="text-xs text-slate-500">All systems operational</span>
        </div>
        <button className="relative p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
          <Bell className="w-4 h-4" />
        </button>
        <div className="w-8 h-8 rounded-full bg-ocean-600 flex items-center justify-center text-white text-xs font-bold">
          {user?.full_name?.[0]?.toUpperCase() || 'U'}
        </div>
      </div>
    </header>
  )
}
