import type { SonarFingerprint } from '../../types'

interface Props {
  fingerprint: SonarFingerprint
  evidenceScore: number
  fpRisk: string
}

const WEIGHTS: Record<string, number> = {
  backscatter_score: 0.15, texture_score: 0.15, geometry_score: 0.15,
  shadow_score: 0.20, object_shadow_score: 0.15,
  seabed_context_score: 0.10, signal_quality_score: 0.10,
}
const LABELS: Record<string, string> = {
  backscatter_score: 'Backscatter', texture_score: 'Texture',
  geometry_score: 'Geometry', shadow_score: 'Shadow',
  object_shadow_score: 'Obj-Shadow', seabed_context_score: 'Seabed',
  signal_quality_score: 'Signal',
}

export default function EvidenceBar({ fingerprint, evidenceScore, fpRisk }: Props) {
  const riskColors: Record<string, string> = {
    LOW: 'bg-emerald-500', MEDIUM: 'bg-amber-500', HIGH: 'bg-red-500',
  }
  const riskText: Record<string, string> = {
    LOW: 'text-emerald-700', MEDIUM: 'text-amber-700', HIGH: 'text-red-700',
  }

  return (
    <div className="space-y-4">
      {/* Overall evidence score */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 mb-0.5">Prototype Evidence Score*</p>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-bold text-navy-900">{evidenceScore.toFixed(0)}</span>
            <span className="text-lg text-slate-400">/100</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500 mb-0.5">False Positive Risk</p>
          <span className={`text-lg font-bold ${riskText[fpRisk] || 'text-slate-700'}`}>{fpRisk}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-ocean-600 rounded-full transition-all duration-700"
          style={{ width: `${Math.min(100, evidenceScore)}%` }}
        />
      </div>

      {/* Cue contributions */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Cue Contributions</p>
        {Object.entries(WEIGHTS).map(([k, w]) => {
          const score = (fingerprint as unknown as Record<string, number>)[k] ?? 0
          const contrib = w * score
          return (
            <div key={k} className="flex items-center gap-3">
              <span className="text-xs text-slate-500 w-20 shrink-0">{LABELS[k]}</span>
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-ocean-500 rounded-full"
                  style={{ width: `${Math.min(100, score)}%`, opacity: 0.6 + w }}
                />
              </div>
              <span className="text-xs font-mono text-slate-600 w-10 text-right">{contrib.toFixed(1)}</span>
            </div>
          )
        })}
      </div>

      <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-xs text-slate-500">
        <strong>Note:</strong> Evidence fusion weights are configurable demonstration values — not scientifically validated coefficients.
        Configuration: v0.1-demo
      </div>
    </div>
  )
}
