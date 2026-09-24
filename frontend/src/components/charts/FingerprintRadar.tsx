import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import type { SonarFingerprint } from '../../types'
import { fingerprintCueLabel } from '../../utils'

interface Props {
  fingerprint: SonarFingerprint
}

const CUE_KEYS: (keyof SonarFingerprint)[] = [
  'backscatter_score','texture_score','geometry_score',
  'shadow_score','object_shadow_score','seabed_context_score','signal_quality_score'
]
const CUE_DISPLAY = [
  'Backscatter','Texture','Geometry',
  'Acoustic Shadow','Obj-Shadow','Seabed Ctx','Signal Quality'
]

function statusColor(score: number) {
  if (score >= 70) return 'text-emerald-700 bg-emerald-50 border-emerald-200'
  if (score >= 40) return 'text-amber-700 bg-amber-50 border-amber-200'
  return 'text-red-700 bg-red-50 border-red-200'
}
function statusLabel(score: number) {
  if (score >= 70) return 'STRONG'
  if (score >= 40) return 'MODERATE'
  return 'WEAK'
}

export default function FingerprintRadar({ fingerprint }: Props) {
  const data = CUE_KEYS.map((k, i) => ({
    subject: CUE_DISPLAY[i],
    score: fingerprint[k] as number,
    fullMark: 100,
  }))

  return (
    <div>
      {/* Radar chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="#E2E8F0" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'Inter, sans-serif' }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fontSize: 8, fill: '#94A3B8' }}
              tickCount={6}
            />
            <Radar
              name="Score"
              dataKey="score"
              stroke="#0077B6"
              fill="#0077B6"
              fillOpacity={0.25}
              strokeWidth={2}
            />
            <Tooltip
              formatter={(v: number) => [`${v}`, 'Score']}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* 7-cue cards */}
      <div className="grid grid-cols-4 gap-2 mt-4">
        {CUE_KEYS.map((k, i) => {
          const score = fingerprint[k] as number
          return (
            <div key={k} className="bg-slate-50 border border-slate-100 rounded-lg p-2.5 text-center">
              <p className="text-xs text-slate-500 mb-1 truncate">{CUE_DISPLAY[i]}</p>
              <p className="text-lg font-bold text-navy-900">{score.toFixed(0)}</p>
              <span className={`text-xs font-semibold px-1.5 py-0.5 rounded border ${statusColor(score)}`}>
                {statusLabel(score)}
              </span>
            </div>
          )
        })}
        {/* Evidence score */}
        <div className="bg-ocean-50 border border-ocean-200 rounded-lg p-2.5 text-center">
          <p className="text-xs text-ocean-600 mb-1 font-medium">Evidence*</p>
          <p className="text-lg font-bold text-ocean-800">{fingerprint.evidence_score?.toFixed(0) ?? '—'}</p>
          <span className="text-xs text-ocean-500">FUSED</span>
        </div>
      </div>
      <p className="text-xs text-slate-400 mt-2">
        * Prototype evidence score — not a scientifically validated probability.
      </p>
    </div>
  )
}
