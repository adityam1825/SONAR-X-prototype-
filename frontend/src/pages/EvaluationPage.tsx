import { useEffect, useState } from 'react'
import { BarChart3, AlertTriangle, Info } from 'lucide-react'
import { evaluationAPI } from '../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'
import { PageLoader } from '../components/ui/LoadingSpinner'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell
} from 'recharts'

interface EvalRun {
  id: string
  model_version: string
  configuration_version: string
  inference_mode: string
  timestamp: string
  metrics: Record<string, number | null>
  per_class_metrics: Record<string, Record<string, number | null>>
  dataset: { name: string; synthetic: boolean; image_count: number; object_count: number }
  notes: string
  small_sample_warning: boolean
  synthetic_data_warning: boolean
}

interface EvalResponse {
  status: 'NOT_EVALUATED' | 'HAS_RUNS'
  message?: string
  runs?: EvalRun[]
}

function MetricCell({ label, value }: { label: string; value: number | null | undefined }) {
  if (value == null) {
    return (
      <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-center">
        <p className="text-xs text-slate-400">{label}</p>
        <p className="text-lg font-bold text-slate-300 mt-1">N/A</p>
        <p className="text-xs text-slate-400">Not computed</p>
      </div>
    )
  }
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3 text-center">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-xl font-bold text-navy-900 mt-1">{(value * 100).toFixed(1)}%</p>
    </div>
  )
}

export default function EvaluationPage() {
  const [data, setData] = useState<EvalResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    evaluationAPI.runs()
      .then(r => setData(r.data as EvalResponse))
      .catch(() => setData({ status: 'NOT_EVALUATED', message: 'Could not reach evaluation API.' }))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <PageLoader text="Loading evaluation metrics…" />

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <PageHeader
        title="Evaluation Metrics"
        subtitle="System performance evaluation — prototype only"
        breadcrumbs={[{ label: 'Evaluation' }]}
      />

      {/* Architecture note */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <Info className="w-4 h-4 mt-0.5 shrink-0" />
        <div>
          <strong>Evaluation Integrity Policy:</strong> Metrics are only displayed when a genuine held-out
          evaluation run exists. Fake accuracy values (e.g. "95% precision") are never displayed.
          Synthetic/demo datasets are clearly labelled.
        </div>
      </div>

      {data?.status === 'NOT_EVALUATED' && (
        <Card>
          <CardBody className="py-16 text-center">
            <BarChart3 className="w-16 h-16 mx-auto text-slate-200 mb-4" />
            <p className="text-2xl font-bold text-slate-700 mb-2">NOT EVALUATED</p>
            <p className="text-slate-500 max-w-lg mx-auto text-sm">
              {data.message || 'No evaluation runs exist for this system.'}
            </p>
            <p className="text-slate-400 text-sm mt-3">
              Evaluation metrics will only be shown when a genuine held-out evaluation is performed
              on a documented dataset. No fake values will be substituted.
            </p>

            {/* Architecture explanation */}
            <div className="mt-8 text-left max-w-2xl mx-auto">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                Evaluation Architecture (ready when data is available)
              </p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { category: 'Detection', metrics: ['Precision', 'Recall', 'F1', 'mAP@0.5', 'FP/image'] },
                  { category: 'Classification', metrics: ['Per-class P/R/F1', 'Macro F1', 'Confusion matrix', 'Unknown rate'] },
                  { category: 'Robustness', metrics: ['By signal quality', 'By noise level', 'By contrast', 'By shadow strength'] },
                  { category: 'Temporal', metrics: ['Correct associations', 'False matches', 'Missed assoc.', 'Distance error'] },
                ].map(({ category, metrics }) => (
                  <div key={category} className="bg-slate-50 rounded-lg p-3">
                    <p className="text-xs font-semibold text-slate-600 mb-2">{category}</p>
                    {metrics.map(m => (
                      <p key={m} className="text-xs text-slate-400 py-0.5 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-200 shrink-0" />{m}
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {data?.status === 'HAS_RUNS' && data.runs && data.runs.map(run => (
        <div key={run.id} className="space-y-4">
          {/* Dataset warnings */}
          {run.synthetic_data_warning && (
            <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-700">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <strong>Synthetic data — not field performance.</strong> Metrics reflect performance on synthetic/demo data only.
            </div>
          )}
          {run.small_sample_warning && (
            <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700">
              <Info className="w-4 h-4 shrink-0" />
              <strong>Indicative only — small sample.</strong> Results are not statistically reliable.
            </div>
          )}

          {/* Run info */}
          <Card>
            <CardHeader><CardTitle>Evaluation Run Information</CardTitle></CardHeader>
            <CardBody>
              <dl className="grid grid-cols-3 gap-4 text-sm">
                {[
                  ['Model Version', run.model_version],
                  ['Config Version', run.configuration_version],
                  ['Inference Mode', run.inference_mode],
                  ['Run Date', new Date(run.timestamp).toLocaleDateString()],
                  ['Dataset', run.dataset.name],
                  ['Images', run.dataset.image_count.toString()],
                ].map(([k, v]) => (
                  <div key={k}><dt className="text-xs text-slate-400">{k}</dt><dd className="font-medium text-navy-900">{v}</dd></div>
                ))}
              </dl>
            </CardBody>
          </Card>

          {/* Overall metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Detection Metrics</CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">
                Computed on held-out test split — test split not used for threshold tuning
              </p>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-5 gap-3">
                {['precision', 'recall', 'f1', 'map_05', 'fp_per_image'].map(k => (
                  <MetricCell key={k} label={k.replace('_', ' ').toUpperCase()} value={run.metrics?.[k]} />
                ))}
              </div>
            </CardBody>
          </Card>

          {/* Per-class metrics */}
          {Object.keys(run.per_class_metrics ?? {}).length > 0 && (
            <Card>
              <CardHeader><CardTitle>Per-Class Metrics</CardTitle></CardHeader>
              <CardBody>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={Object.entries(run.per_class_metrics).map(([cls, m]) => ({
                      name: cls.replace('_', ' '),
                      F1: m?.f1 != null ? +(m.f1 * 100).toFixed(1) : null,
                    }))}>
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                      <Tooltip formatter={(v: number) => [`${v}%`, 'F1']} />
                      <Bar dataKey="F1" radius={[4, 4, 0, 0]}>
                        {Object.keys(run.per_class_metrics).map((_, i) => (
                          <Cell key={i} fill={['#2563EB','#059669','#7C3AED','#EA580C'][i % 4]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>
          )}

          {run.notes && (
            <Card>
              <CardHeader><CardTitle>Notes</CardTitle></CardHeader>
              <CardBody><p className="text-sm text-slate-600">{run.notes}</p></CardBody>
            </Card>
          )}
        </div>
      ))}
    </div>
  )
}
