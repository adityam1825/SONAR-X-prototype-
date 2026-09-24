import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch, MapPin, Calendar, ArrowRight, CheckCircle } from 'lucide-react'
import { detectionsAPI } from '../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'
import { PageLoader } from '../components/ui/LoadingSpinner'
import SonarMap from '../components/map/SonarMap'
import type { DebrisObject } from '../types'

export default function TemporalIntelligencePage() {
  const [debrisObjects, setDebrisObjects] = useState<DebrisObject[]>([])
  const [selected, setSelected] = useState<DebrisObject | null>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [verifyComment, setVerifyComment] = useState('')
  const [verifyMsg, setVerifyMsg] = useState('')

  useEffect(() => {
    detectionsAPI.debrisList().then(r => {
      const d = r.data as { results?: DebrisObject[] } | DebrisObject[]
      const list = Array.isArray(d) ? d : d.results ?? []
      setDebrisObjects(list)
      if (list.length > 0) setSelected(list[0])
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const doVerify = async (decision: 'CONFIRMED' | 'REJECTED') => {
    if (!selected) return
    setVerifying(true)
    try {
      await detectionsAPI.debrisVerifyTemporal(selected.debris_uid, {
        decision, comment: verifyComment
      })
      setVerifyMsg(`Temporal case verified as ${decision}.`)
      // Refresh
      const r = await detectionsAPI.debrisList()
      const d = r.data as { results?: DebrisObject[] } | DebrisObject[]
      setDebrisObjects(Array.isArray(d) ? d : d.results ?? [])
    } catch { setVerifyMsg('Verification failed.') }
    finally { setVerifying(false) }
  }

  const statusColor: Record<string, string> = {
    STILL_PRESENT: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    NOT_DETECTED: 'bg-slate-50 text-slate-600 border-slate-200',
    POTENTIALLY_RELOCATED: 'bg-purple-50 text-purple-700 border-purple-200',
    POSSIBLE_MATCH: 'bg-blue-50 text-blue-700 border-blue-200',
    NEW_DETECTION: 'bg-ocean-50 text-ocean-700 border-ocean-200',
    REQUIRES_VERIFICATION: 'bg-amber-50 text-amber-700 border-amber-200',
  }

  if (loading) return <PageLoader text="Loading temporal intelligence…" />

  // Find prev/candidate locations for demo
  const prevObs = selected?.observations?.[0]
  const candObs = selected?.observations?.[1]

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <PageHeader
        title="Temporal Intelligence"
        subtitle="Track debris objects across repeat surveys"
        breadcrumbs={[{ label: 'Temporal Intelligence' }]}
      />

      <div className="grid grid-cols-3 gap-6">
        {/* Debris list */}
        <div className="col-span-1">
          <Card>
            <CardHeader><CardTitle>Tracked Objects ({debrisObjects.length})</CardTitle></CardHeader>
            <CardBody className="p-0">
              {debrisObjects.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm px-4">
                  No tracked objects. Run repeat surveys to enable temporal tracking.
                </div>
              ) : (
                <div className="divide-y divide-slate-50">
                  {debrisObjects.map(obj => (
                    <button
                      key={obj.debris_uid}
                      onClick={() => { setSelected(obj); setVerifyMsg('') }}
                      className={`w-full text-left px-4 py-3.5 hover:bg-slate-50 transition-colors ${selected?.debris_uid === obj.debris_uid ? 'bg-ocean-50 border-l-2 border-ocean-500' : ''}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono font-bold text-navy-900 text-sm">{obj.debris_uid}</span>
                        {obj.is_demo && <span className="text-xs font-bold text-amber-600">DEMO</span>}
                      </div>
                      <span className={`text-xs font-semibold px-1.5 py-0.5 rounded border ${statusColor[obj.current_status] ?? 'bg-slate-50 text-slate-600'}`}>
                        {obj.current_status.replace(/_/g, ' ')}
                      </span>
                      <p className="text-xs text-slate-400 mt-1">
                        {obj.observations?.length ?? 0} observations
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Selected detail */}
        {selected && (
          <div className="col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-xl text-navy-900">{selected.debris_uid}</span>
                    <span className={`text-sm font-bold px-2 py-0.5 rounded border ${statusColor[selected.current_status] ?? 'bg-slate-50 text-slate-600'}`}>
                      {selected.current_status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {selected.is_demo && <span className="text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">DATA SOURCE: DEMO</span>}
                </div>
              </CardHeader>
              <CardBody>
                {/* Timeline */}
                <div className="space-y-4 mb-4">
                  {selected.observations?.map((obs, i) => (
                    <div key={obs.id} className="flex items-start gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${i === 0 ? 'border-ocean-500 bg-ocean-50' : 'border-purple-500 bg-purple-50'}`}>
                          <span className="text-xs font-bold">{i + 1}</span>
                        </div>
                        {i < (selected.observations?.length ?? 1) - 1 && (
                          <div className="w-0.5 h-8 bg-slate-200 mt-1" />
                        )}
                      </div>
                      <div className="flex-1 bg-slate-50 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-navy-900">{obs.survey_name ?? obs.survey_id}</span>
                          <span className="text-xs text-slate-400">{new Date(obs.timestamp).toLocaleDateString()}</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                          <div><span className="text-slate-400">Class:</span> <span className="font-medium">{obs.classification?.replace(/_/g,' ') || '—'}</span></div>
                          <div><span className="text-slate-400">Confidence*:</span> <span className="font-medium">{obs.confidence?.toFixed(0)}</span></div>
                          <div><span className="text-slate-400">Hazard:</span> <span className="font-medium">{obs.hazard_level}</span></div>
                        </div>
                        {obs.latitude != null && (
                          <p className="text-xs font-mono text-slate-500 mt-1">
                            {obs.latitude.toFixed(5)}°N, {obs.longitude?.toFixed(5)}°E
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Potentially relocated details */}
                {selected.current_status === 'POTENTIALLY_RELOCATED' && prevObs && candObs && (
                  <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-5 h-5 text-purple-600" />
                      <p className="font-bold text-purple-800">POTENTIALLY RELOCATED</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-xs text-slate-500 mb-1 flex items-center gap-1"><MapPin className="w-3 h-3" /> Previous Location</p>
                        <p className="font-mono text-xs">{prevObs.latitude?.toFixed(5)}°N, {prevObs.longitude?.toFixed(5)}°E</p>
                        <p className="text-xs text-slate-400">{prevObs.survey_name ?? prevObs.survey_id}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1 flex items-center gap-1"><MapPin className="w-3 h-3 text-purple-500" /> Candidate Location</p>
                        <p className="font-mono text-xs">{candObs.latitude?.toFixed(5)}°N, {candObs.longitude?.toFixed(5)}°E</p>
                        <p className="text-xs text-slate-400">{candObs.survey_name ?? candObs.survey_id}</p>
                      </div>
                    </div>
                    <p className="text-xs text-purple-700 bg-purple-100 rounded p-2">
                      Object not detected at original location. Nearby candidate found with similar sonar fingerprint.
                      <strong> This is NOT confirmed movement.</strong> A missing detection does NOT prove the object moved.
                      Human verification required.
                    </p>
                  </div>
                )}

                {selected.current_status === 'NOT_DETECTED' && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
                    <strong>NOT DETECTED</strong> — Object not found in follow-up survey. No plausible nearby candidate.
                    This does NOT prove the object was removed. May be undetected due to survey geometry, conditions, or nadir overlap.
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Map showing relocation */}
            {prevObs?.latitude != null && candObs?.latitude != null && (
              <Card>
                <CardHeader><CardTitle>Spatial Comparison</CardTitle></CardHeader>
                <CardBody>
                  <div style={{ height: 300 }}>
                    <SonarMap
                      detections={[]}
                      center={[prevObs.latitude, prevObs.longitude!]}
                      zoom={14}
                      showTemporalLine
                      previousLocation={{ lat: prevObs.latitude, lng: prevObs.longitude!, label: 'Survey 1' }}
                      candidateLocation={{ lat: candObs.latitude, lng: candObs.longitude!, label: 'Candidate' }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    Dashed line: POTENTIAL RELOCATION PATH — not confirmed movement.
                    Distance is approximate (Haversine formula).
                  </p>
                </CardBody>
              </Card>
            )}

            {/* Verification */}
            {(selected.current_status === 'POTENTIALLY_RELOCATED' || selected.current_status === 'REQUIRES_VERIFICATION') && (
              <Card>
                <CardHeader><CardTitle>Temporal Verification</CardTitle></CardHeader>
                <CardBody className="space-y-3">
                  <textarea
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ocean-500"
                    rows={2} value={verifyComment} onChange={e => setVerifyComment(e.target.value)}
                    placeholder="Reviewer comment…"
                  />
                  {verifyMsg && <p className="text-sm text-emerald-600">{verifyMsg}</p>}
                  <div className="flex gap-3">
                    <button
                      onClick={() => doVerify('CONFIRMED')} disabled={verifying}
                      className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium"
                    >
                      <CheckCircle className="w-4 h-4" /> Confirm Relocation
                    </button>
                    <button
                      onClick={() => doVerify('REJECTED')} disabled={verifying}
                      className="flex items-center gap-2 bg-slate-600 hover:bg-slate-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium"
                    >
                      Not Relocated
                    </button>
                  </div>
                  <p className="text-xs text-slate-400">
                    Verification is stored in the audit trail. Confirming means the reviewer believes this is the same object at a new location.
                  </p>
                </CardBody>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
