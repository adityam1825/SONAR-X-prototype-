import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Filter, ExternalLink, Map, Download } from 'lucide-react'
import { detectionsAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import { ClassBadge, HazardBadge, RiskBadge, VerificationBadge, DemoBadge, InferenceModeBadge } from '../../components/ui/StatusChip'
import PageHeader from '../../components/ui/PageHeader'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import type { Detection, Classification, HazardLevel } from '../../types'

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const [detections, setDetections] = useState<Detection[]>([])
  const [loading, setLoading] = useState(true)
  const [filterClass, setFilterClass] = useState('')
  const [filterHazard, setFilterHazard] = useState('')
  const [filterVerification, setFilterVerification] = useState('')

  useEffect(() => {
    if (!id) return
    detectionsAPI.list({ survey: id }).then(r => {
      const data = r.data as { results?: Detection[] } | Detection[]
      setDetections(Array.isArray(data) ? data : data.results ?? [])
    }).catch(console.error).finally(() => setLoading(false))
  }, [id])

  if (loading) return <PageLoader text="Loading detections…" />

  const filtered = detections.filter(d => {
    if (filterClass && d.classification !== filterClass) return false
    if (filterHazard && d.hazard_level !== filterHazard) return false
    if (filterVerification && d.verification_status !== filterVerification) return false
    return true
  })

  const stats = {
    total: detections.length,
    hazards: detections.filter(d => d.hazard_level !== 'NONE').length,
    pending: detections.filter(d => d.verification_status === 'PENDING').length,
    debris: detections.filter(d => d.classification === 'MARINE_DEBRIS').length,
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <PageHeader
        title="Detection Results"
        subtitle={`${detections.length} total detections`}
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Results' }]}
        actions={
          <div className="flex gap-2">
            <Link to={`/surveys/${id}/map`}
              className="flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              <Map className="w-4 h-4" /> Map View
            </Link>
            <Link to={`/surveys/${id}/export`}
              className="flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              <Download className="w-4 h-4" /> Export
            </Link>
          </div>
        }
      />

      {/* Mini stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: stats.total, color: 'text-navy-900' },
          { label: 'Marine Debris', value: stats.debris, color: 'text-blue-700' },
          { label: 'Hazard Flags', value: stats.hazards, color: 'text-red-600' },
          { label: 'Pending Verification', value: stats.pending, color: 'text-amber-600' },
        ].map(({ label, value, color }) => (
          <Card key={label}>
            <CardBody className="py-3">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-slate-500">{label}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card>
        <CardBody className="flex flex-wrap gap-4 py-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-500">Filter:</span>
          </div>
          <select
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-ocean-400"
            value={filterClass} onChange={e => setFilterClass(e.target.value)}
          >
            <option value="">All Classes</option>
            <option value="MARINE_DEBRIS">Marine Debris</option>
            <option value="NATURAL_FORMATION">Natural Formation</option>
            <option value="SONAR_ARTIFACT">Sonar Artifact</option>
            <option value="UNKNOWN_ANOMALY">Unknown Anomaly</option>
          </select>
          <select
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-ocean-400"
            value={filterHazard} onChange={e => setFilterHazard(e.target.value)}
          >
            <option value="">All Hazard Levels</option>
            <option value="NONE">None</option>
            <option value="CAUTION">Caution</option>
            <option value="HIGH_CAUTION">High Caution</option>
          </select>
          <select
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-ocean-400"
            value={filterVerification} onChange={e => setFilterVerification(e.target.value)}
          >
            <option value="">All Verification States</option>
            <option value="PENDING">Pending</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="REJECTED">Rejected</option>
          </select>
          <span className="ml-auto text-xs text-slate-400">{filtered.length} showing</span>
        </CardBody>
      </Card>

      {/* Detection table */}
      {filtered.length === 0 ? (
        <Card>
          <CardBody>
            <div className="text-center py-12 text-slate-400">
              <p className="text-lg font-medium mb-1">No detections found</p>
              <p className="text-sm">Run the analysis pipeline first, or adjust filters.</p>
            </div>
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardBody className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    {['UID', 'Class', 'Conf.*', 'Evidence*', 'Risk', 'Hazard', 'Verification', 'Mode', 'Source', 'Location', ''].map(h => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {filtered.map(det => (
                    <tr key={det.id} className={`hover:bg-slate-50 transition-colors ${det.hazard_level === 'HIGH_CAUTION' ? 'bg-red-50/40' : ''}`}>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-slate-600">{det.detection_uid}</span>
                        {det.debris_uid && <div className="text-xs text-ocean-500 font-mono">{det.debris_uid}</div>}
                      </td>
                      <td className="px-4 py-3"><ClassBadge c={det.classification} /></td>
                      <td className="px-4 py-3 font-semibold text-navy-900">{det.confidence?.toFixed(0)}</td>
                      <td className="px-4 py-3 text-slate-600">{det.evidence_score?.toFixed(0)}</td>
                      <td className="px-4 py-3"><RiskBadge risk={det.false_positive_risk} /></td>
                      <td className="px-4 py-3"><HazardBadge level={det.hazard_level} /></td>
                      <td className="px-4 py-3"><VerificationBadge status={det.verification_status} /></td>
                      <td className="px-4 py-3"><InferenceModeBadge mode={det.inference_mode} /></td>
                      <td className="px-4 py-3">{det.data_source === 'DEMO' && <DemoBadge />}</td>
                      <td className="px-4 py-3 text-xs font-mono text-slate-500">
                        {det.latitude != null
                          ? `${det.latitude.toFixed(4)}, ${det.longitude?.toFixed(4)}`
                          : <span className="italic text-slate-300">No GPS</span>
                        }
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/detections/${det.id}`}
                          className="flex items-center gap-1 text-xs text-ocean-600 hover:underline whitespace-nowrap"
                        >
                          Details <ExternalLink className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 border-t border-slate-50 bg-slate-50/50">
              <p className="text-xs text-slate-400">
                * Confidence and Evidence Score are prototype heuristic values — NOT validated probabilities or model accuracy.
                Inference Mode: {[...new Set(filtered.map(d => d.inference_mode))].join(', ') || '—'}
              </p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
