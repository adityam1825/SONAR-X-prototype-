import { cn } from '../../utils'

interface BadgeProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'outline'
}

export function Badge({ children, className, variant = 'default' }: BadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border',
      variant === 'outline' ? 'bg-transparent' : '',
      className
    )}>
      {children}
    </span>
  )
}
