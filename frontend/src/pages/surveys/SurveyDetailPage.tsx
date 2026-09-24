import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  Upload, Shield, Map, Download, Clock, Play,
  CheckCircle, Activity, FileText
} from 'lucide-react'
import { surveysAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import { DemoBadge } from '../../components/ui/StatusChip'
import PageHeader from '../../components/ui/PageHeader'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import type { Survey } from '../../types'

const PIPELINE_STEPS = [
  { num: '01', label: 'DATA INGESTION', route: 'upload', icon: Upload },
  { num: '02', label: 'VALIDATION', route: 'validation', icon: CheckCircle },
  { num: '03', label: 'SONAR PREPROCESSING', route: 'preprocessing', icon: Activity },
  { num: '04', label: 'CANDIDATE DETECTION', route: 'analysis', icon: Play },
  { num: '05', label: 'RESULTS', route: 'results', icon: FileText },
  { num: '06', label: 'GEOSPATIAL MAP', route: 'map', icon: Map },
  { num: '07', label: 'EXPORT', route: 'export', icon: Download },
  { num: '08', label: 'TEMPORAL ANALYSIS', route: 'temporal', icon: Clock },
]

export default function SurveyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [survey, setSurvey] = useState<Survey | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    if (!id) return
    surveysAPI.get(id).then(r => setSurvey(r.data as Survey)).catch(console.error).finally(() => setLoading(false))
  }, [id])

  const runAnalysis = async () => {
    if (!id) return
    setAnalyzing(true)
    try {
      await surveysAPI.analyze(id)
      navigate(`/surveys/${id}/results`)
    } catch (e) {
      console.error(e)
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading || !survey) return <PageLoader text="Loading survey…" />

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <PageHeader
        title={survey.name}
        subtitle={`Survey ${survey.survey_id} · ${survey.date}`}
        breadcrumbs={[{ label: survey.name }]}
        badge={survey.is_demo ? <DemoBadge /> : undefined}
        actions={
          <button
            onClick={runAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Play className="w-4 h-4" />
            {analyzing ? 'Running…' : 'Run Analysis'}
          </button>
        }
      />

      {survey.is_demo && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-700">
          <strong>DATA SOURCE: DEMO</strong> — Synthetic data — not field performance.
          All results are demonstration outputs for SIH presentation.
        </div>
      )}

      <div className="grid grid-cols-3 gap-5">
        {/* Survey info */}
        <div className="col-span-2 space-y-4">
          <Card>
            <CardHeader><CardTitle>Survey Information</CardTitle></CardHeader>
            <CardBody>
              <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
                {[
                  ['Survey ID', survey.survey_id],
                  ['Status', survey.status],
                  ['Date', survey.date],
                  ['Data Source', survey.data_source],
                  ['Area', survey.area || '—'],
                  ['Operator', survey.operator || '—'],
                  ['Detections', survey.detection_count?.toString() ?? '0'],
                  ['Channel', survey.channel_layout],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-xs text-slate-400 font-medium">{k}</dt>
                    <dd className="text-navy-900 font-medium mt-0.5">{v}</dd>
                  </div>
                ))}
              </dl>
            </CardBody>
          </Card>

          <Card>
            <CardHeader><CardTitle>Sonar Metadata</CardTitle></CardHeader>
            <CardBody>
              <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
                <div>
                  <dt className="text-xs text-slate-400 font-medium">Altitude above seabed</dt>
                  <dd className="text-navy-900 mt-0.5">{survey.altitude_m != null ? `${survey.altitude_m} m` : <span className="text-slate-400 italic">Not available</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-400 font-medium">Range scale</dt>
                  <dd className="text-navy-900 mt-0.5">{survey.range_scale_mpp != null ? `${survey.range_scale_mpp} m/px` : <span className="text-slate-400 italic">Not available</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-400 font-medium">Gain corrected</dt>
                  <dd className="mt-0.5">{survey.already_gain_corrected ? <span className="text-emerald-600">Yes</span> : <span className="text-slate-400">No</span>}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-400 font-medium">Slant-range corrected</dt>
                  <dd className="mt-0.5">{survey.already_slant_range_corrected ? <span className="text-emerald-600">Yes</span> : <span className="text-slate-400">No</span>}</dd>
                </div>
              </dl>
              {survey.altitude_m == null && (
                <p className="text-xs text-amber-600 mt-3 bg-amber-50 border border-amber-100 rounded px-3 py-2">
                  Slant-range correction will be skipped — altitude unavailable.
                </p>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Pipeline */}
        <div>
          <Card>
            <CardHeader><CardTitle>Analysis Pipeline</CardTitle></CardHeader>
            <CardBody className="p-0">
              <div className="divide-y divide-slate-50">
                {PIPELINE_STEPS.map(({ num, label, route, icon: Icon }) => (
                  <Link
                    key={route}
                    to={`/surveys/${id}/${route}`}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors group"
                  >
                    <span className="text-xs font-mono text-slate-300 w-6 shrink-0">{num}</span>
                    <Icon className="w-3.5 h-3.5 text-slate-400 group-hover:text-ocean-600 shrink-0" />
                    <span className="text-xs font-medium text-slate-600 group-hover:text-navy-900">{label}</span>
                  </Link>
                ))}
              </div>
            </CardBody>
          </Card>

          {/* Location */}
          {survey.latitude != null && (
            <Card className="mt-4">
              <CardHeader><CardTitle>Location</CardTitle></CardHeader>
              <CardBody>
                <p className="text-xs font-mono text-slate-600">
                  {survey.latitude.toFixed(4)}°N, {survey.longitude?.toFixed(4)}°E
                </p>
              </CardBody>
            </Card>
          )}
        </div>
      </div>

      {/* Notes */}
      {survey.notes && (
        <Card>
          <CardHeader><CardTitle>Notes</CardTitle></CardHeader>
          <CardBody>
            <p className="text-sm text-slate-600">{survey.notes}</p>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
