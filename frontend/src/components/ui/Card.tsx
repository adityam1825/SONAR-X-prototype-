import { cn } from '../../utils'

interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn('bg-white rounded-xl border border-slate-200 shadow-sm', className)}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: CardProps) {
  return <div className={cn('px-6 py-4 border-b border-slate-100', className)}>{children}</div>
}

export function CardBody({ children, className }: CardProps) {
  return <div className={cn('px-6 py-4', className)}>{children}</div>
}

export function CardTitle({ children, className }: CardProps) {
  return <h3 className={cn('font-semibold text-navy-900 text-sm', className)}>{children}</h3>
}
