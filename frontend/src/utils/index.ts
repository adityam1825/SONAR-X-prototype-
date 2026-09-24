import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { Classification, HazardLevel, FPRisk, VerificationStatus } from '../types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function classificationLabel(c: Classification): string {
  return {
    MARINE_DEBRIS: 'Marine Debris',
    NATURAL_FORMATION: 'Natural Formation',
    SONAR_ARTIFACT: 'Sonar Artifact',
    UNKNOWN_ANOMALY: 'Unknown Anomaly',
  }[c] ?? c
}

export function classificationColor(c: Classification): string {
  return {
    MARINE_DEBRIS: 'bg-blue-100 text-blue-800 border-blue-200',
    NATURAL_FORMATION: 'bg-green-100 text-green-800 border-green-200',
    SONAR_ARTIFACT: 'bg-purple-100 text-purple-800 border-purple-200',
    UNKNOWN_ANOMALY: 'bg-orange-100 text-orange-800 border-orange-200',
  }[c] ?? 'bg-slate-100 text-slate-700'
}

export function hazardColor(level: HazardLevel): string {
  return {
    NONE: 'bg-slate-100 text-slate-600 border-slate-200',
    CAUTION: 'bg-amber-100 text-amber-800 border-amber-200',
    HIGH_CAUTION: 'bg-red-100 text-red-800 border-red-200',
  }[level] ?? 'bg-slate-100 text-slate-600'
}

export function riskColor(risk: FPRisk): string {
  return {
    LOW: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    MEDIUM: 'text-amber-700 bg-amber-50 border-amber-200',
    HIGH: 'text-red-700 bg-red-50 border-red-200',
  }[risk] ?? 'text-slate-600'
}

export function verificationColor(vs: VerificationStatus): string {
  return {
    PENDING: 'bg-amber-50 text-amber-700 border-amber-200',
    CONFIRMED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    REJECTED: 'bg-red-50 text-red-700 border-red-200',
    ESCALATED: 'bg-purple-50 text-purple-700 border-purple-200',
    CLASS_CHANGED: 'bg-blue-50 text-blue-700 border-blue-200',
  }[vs] ?? 'bg-slate-50 text-slate-600'
}

export function statusStepColor(status: string): string {
  switch (status) {
    case 'APPLIED': case 'COMPLETE': return 'text-emerald-700 bg-emerald-50'
    case 'ESTIMATED': return 'text-blue-700 bg-blue-50'
    case 'SKIPPED': return 'text-slate-500 bg-slate-50'
    case 'NOT_APPLIED': return 'text-slate-400 bg-slate-50'
    case 'FAILED': return 'text-red-700 bg-red-50'
    default: return 'text-slate-500 bg-slate-50'
  }
}

export function fingerprintCueLabel(cue: string): string {
  return {
    backscatter: 'Backscatter',
    texture: 'Texture',
    geometry: 'Geometry',
    shadow: 'Acoustic Shadow',
    object_shadow: 'Object-Shadow',
    seabed_context: 'Seabed Context',
    signal_quality: 'Signal Quality',
  }[cue] ?? cue
}
