import { AlertTriangle, ShieldAlert, Shield } from 'lucide-react'
import type { HazardLevel } from '../../types'

interface Props {
  level: HazardLevel
  score: number
  indicators: string[]
  limitedData: boolean
  recommendedAction: string
}

export default function HazardPanel({ level, score, indicators, limitedData, recommendedAction }: Props) {
  if (level === 'NONE') {
    return (
      <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-xl p-4">
        <Shield className="w-5 h-5 text-slate-400 shrink-0" />
        <div>
          <p className="font-semibold text-slate-600 text-sm">No Hazard Flag</p>
          <p className="text-xs text-slate-400 mt-0.5">
            No precautionary hazard indicators triggered. Note: absence of a hazard flag does NOT mean the object is safe.
          </p>
        </div>
      </div>
    )
  }

  const isHigh = level === 'HIGH_CAUTION'

  return (
    <div className={`border-2 rounded-xl overflow-hidden ${isHigh ? 'border-red-400' : 'border-amber-400'}`}>
      {/* Banner */}
      <div className={`px-5 py-4 flex items-center gap-3 ${isHigh ? 'bg-red-600' : 'bg-amber-500'}`}>
        <ShieldAlert className="w-7 h-7 text-white shrink-0" />
        <div>
          <p className="text-white font-bold text-lg tracking-wide">POTENTIAL HAZARD — DO NOT DISTURB</p>
          {isHigh && (
            <p className="text-red-100 text-sm font-medium">HIGH PRIORITY — HUMAN VERIFICATION REQUIRED</p>
          )}
        </div>
      </div>

      {/* Details */}
      <div className="bg-white p-5 space-y-4">
        <div className="flex items-center gap-6">
          <div>
            <p className="text-xs text-slate-500">Hazard Level</p>
            <p className={`font-bold text-lg ${isHigh ? 'text-red-700' : 'text-amber-700'}`}>
              {level.replace('_', ' ')}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Hazard Score</p>
            <p className={`font-bold text-lg ${isHigh ? 'text-red-700' : 'text-amber-700'}`}>{score.toFixed(0)}</p>
          </div>
          {limitedData && (
            <div className="bg-amber-50 border border-amber-200 rounded px-3 py-2">
              <p className="text-xs text-amber-700 font-semibold">LIMITED METADATA</p>
              <p className="text-xs text-amber-600">Assessment based on limited data</p>
            </div>
          )}
        </div>

        {indicators.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Triggered Indicators</p>
            <ul className="space-y-1.5">
              {indicators.map((ind, i) => (
                <li key={i} className={`flex items-center gap-2 text-sm ${isHigh ? 'text-red-700' : 'text-amber-700'}`}>
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  {ind}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="bg-slate-50 border border-slate-100 rounded-lg p-3">
          <p className="text-xs font-semibold text-slate-600 mb-1">Recommended Action</p>
          <p className="text-sm text-slate-700">{recommendedAction}</p>
        </div>

        <div className="border-t border-slate-100 pt-3">
          <p className="text-xs text-slate-400">
            This flag is <strong>precautionary only</strong>. This system does NOT identify specific hazardous objects.
            Absence of a hazard flag does NOT mean an object is safe.
          </p>
        </div>
      </div>
    </div>
  )
}
