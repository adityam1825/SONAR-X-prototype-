import { Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'

interface Crumb {
  label: string
  to?: string
}

interface PageHeaderProps {
  title: string
  subtitle?: string
  breadcrumbs?: Crumb[]
  actions?: React.ReactNode
  badge?: React.ReactNode
}

export default function PageHeader({ title, subtitle, breadcrumbs, actions, badge }: PageHeaderProps) {
  return (
    <div className="mb-6">
      {breadcrumbs && (
        <nav className="flex items-center gap-1 text-xs text-slate-400 mb-2">
          <Link to="/dashboard" className="hover:text-slate-600 flex items-center gap-1">
            <Home className="w-3 h-3" /> Dashboard
          </Link>
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-1">
              <ChevronRight className="w-3 h-3" />
              {crumb.to ? (
                <Link to={crumb.to} className="hover:text-slate-600">{crumb.label}</Link>
              ) : (
                <span className="text-slate-600">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-navy-900 truncate">{title}</h1>
            {badge}
          </div>
          {subtitle && <p className="text-slate-500 text-sm mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </div>
    </div>
  )
}
