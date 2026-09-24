import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { GitBranch, Clock, ArrowRight } from 'lucide-react'
import { detectionsAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import type { DebrisObject } from '../../types'

export default function TemporalPage() {
  const { id } = useParams<{ id: string }>()
  const [debrisObjects, setDebrisObjects] = useState<DebrisObject[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    detectionsAPI.debrisList().then(r => {
      const d = r.data as { results?: DebrisObject[] } | DebrisObject[]
      setDebrisObjects(Array.isArray(d) ? d : d.results ?? [])
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <PageLoader text="Loading temporal tracking…" />

  const statusColor: Record<string, string> = {
    STILL_PRESENT: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    NOT_DETECTED: 'bg-slate-50 text-slate-600 border-slate-200',
    POTENTIALLY_RELOCATED: 'bg-purple-50 text-purple-700 border-purple-200',
    POSSIBLE_MATCH: 'bg-blue-50 text-blue-700 border-blue-200',
    NEW_DETECTION: 'bg-ocean-50 text-ocean-700 border-ocean-200',
    REQUIRES_VERIFICATION: 'bg-amber-50 text-amber-700 border-amber-200',
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Temporal Tracking"
        subtitle="Track debris objects across repeat surveys"
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Temporal' }]}
        actions={
          <Link to="/temporal"
            className="flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 px-4 py-2 rounded-lg text-sm">
            <Clock className="w-4 h-4" /> Full Temporal View
          </Link>
        }
      />

      {debrisObjects.length === 0 ? (
        <Card>
          <CardBody>
            <div className="text-center py-10 text-slate-400">
              <GitBranch className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No tracked debris objects yet</p>
              <p className="text-sm mt-1">Objects are tracked after repeat surveys.</p>
            </div>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {debrisObjects.map(obj => (
            <Card key={obj.debris_uid}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-ocean-50 border border-ocean-100 flex items-center justify-center">
                      <GitBranch className="w-5 h-5 text-ocean-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-navy-900">{obj.debris_uid}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${statusColor[obj.current_status] ?? 'bg-slate-50 text-slate-600 border-slate-200'}`}>
                          {obj.current_status.replace(/_/g, ' ')}
                        </span>
                        {obj.is_demo && <span className="text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded">DEMO</span>}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {obj.classification?.replace(/_/g, ' ') || '—'} · {obj.observations?.length ?? 0} observations
                        {obj.first_observed && ` · First: ${new Date(obj.first_observed).toLocaleDateString()}`}
                      </p>
                    </div>
                  </div>
                  <Link to="/temporal"
                    className="flex items-center gap-1 text-xs text-ocean-600 hover:underline">
                    Details <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
                {obj.current_status === 'POTENTIALLY_RELOCATED' && (
                  <div className="mt-3 bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm text-purple-700">
                    <strong>POTENTIALLY RELOCATED</strong> — Object not detected at original location.
                    Nearby candidate with high fingerprint similarity found.
                    Human verification required. This is NOT confirmed movement.
                  </div>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
