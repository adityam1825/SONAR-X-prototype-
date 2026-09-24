import { cn } from '../../utils'
import type { Classification, HazardLevel, FPRisk, VerificationStatus } from '../../types'
import {
  classificationColor, classificationLabel,
  hazardColor, riskColor, verificationColor
} from '../../utils'

export function ClassBadge({ c }: { c: Classification }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border', classificationColor(c))}>
      {classificationLabel(c)}
    </span>
  )
}

export function HazardBadge({ level }: { level: HazardLevel }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border', hazardColor(level))}>
      {level.replace('_', ' ')}
    </span>
  )
}

export function RiskBadge({ risk }: { risk: FPRisk }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border', riskColor(risk))}>
      {risk}
    </span>
  )
}

export function VerificationBadge({ status }: { status: VerificationStatus }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border', verificationColor(status))}>
      {status.replace('_', ' ')}
    </span>
  )
}

export function DemoBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border bg-amber-50 text-amber-700 border-amber-200">
      DEMO
    </span>
  )
}

export function InferenceModeBadge({ mode }: { mode: string }) {
  const colors: Record<string, string> = {
    DEMO: 'bg-amber-50 text-amber-700 border-amber-200',
    CLASSICAL_CV: 'bg-purple-50 text-purple-700 border-purple-200',
    YOLO: 'bg-blue-50 text-blue-700 border-blue-200',
  }
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border', colors[mode] ?? 'bg-slate-50 text-slate-700 border-slate-200')}>
      {mode}
    </span>
  )
}

export function StepStatusChip({ status }: { status: string }) {
  const colors: Record<string, string> = {
    APPLIED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    COMPLETE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    ESTIMATED: 'bg-blue-50 text-blue-700 border-blue-200',
    SKIPPED: 'bg-slate-50 text-slate-500 border-slate-200',
    NOT_APPLIED: 'bg-slate-50 text-slate-400 border-slate-200',
    FAILED: 'bg-red-50 text-red-700 border-red-200',
  }
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border', colors[status] ?? 'bg-slate-50 text-slate-600 border-slate-200')}>
      {status.replace('_', ' ')}
    </span>
  )
}
