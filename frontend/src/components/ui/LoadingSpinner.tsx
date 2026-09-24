import { cn } from '../../utils'

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-center p-8', className)}>
      <div className="w-8 h-8 border-2 border-sonar-cyan border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

export function PageLoader({ text = 'Loading…' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] gap-3">
      <div className="w-10 h-10 border-2 border-sonar-cyan border-t-transparent rounded-full animate-spin" />
      <p className="text-slate-400 text-sm">{text}</p>
    </div>
  )
}
