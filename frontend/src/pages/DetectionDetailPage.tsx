import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { CheckCircle, Clock, ArrowLeft, MapPin, AlertTriangle, GitBranch, Download } from 'lucide-react'
import { detectionsAPI } from '../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../components/ui/Card'
import {
  ClassBadge, HazardBadge, RiskBadge, VerificationBadge,
  DemoBadge, InferenceModeBadge, StepStatusChip
} from '../components/ui/StatusChip'
import PageHeader from '../components/ui/PageHeader'
import { PageLoader } from '../components/ui/LoadingSpinner'
import FingerprintRadar from '../components/charts/FingerprintRadar'
import EvidenceBar from '../components/charts/EvidenceBar'
import HazardPanel from '../components/ui/HazardPanel'
import type { Detection } from '../types'

export default function DetectionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [detection, setDetection] = useState<Detection | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    detectionsAPI.get(id).then(r => setDetection(r.data as Detection))
      .catch(console.error).finally(() => setLoading(false))
  }, [id])

  if (loading) return <PageLoader text="Loading detection…" />
  if (!detection) return <div className="text-center py-20 text-slate-400">Detection not found.</div>

  const fp = detection.fingerprint

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <PageHeader
        title={detection.detection_uid}
        subtitle={`Survey: ${detection.survey_id ?? '—'}`}
        breadcrumbs={[
          { label: 'Surveys', to: '/dashboard' },
          { label: 'Detection' },
        ]}
        badge={
          <div className="flex items-center gap-2">
            {detection.data_source === 'DEMO' && <DemoBadge />}
            <InferenceModeBadge mode={detection.inference_mode} />
          </div>
        }
        actions={
          <div className="flex gap-2">
            <Link to={`/detections/${id}/verify`}
              className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              <CheckCircle className="w-4 h-4" /> Verify
            </Link>
            <button onClick={() => navigate(-1)}
              className="flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 px-3 py-2 rounded-lg text-sm transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          </div>
        }
      />

      {detection.data_source === 'DEMO' && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-xs text-amber-700 font-medium">
          DATA SOURCE: DEMO — Synthetic data — not field performance.
          All scores are demonstration values.
        </div>
      )}

      <div className="grid grid-cols-5 gap-6">
        {/* LEFT: Image panel */}
        <div className="col-span-2 space-y-4">
          <Card>
            <CardHeader><CardTitle>Sonar Image</CardTitle></CardHeader>
            <CardBody>
              {/* Synthetic sonar image placeholder */}
              <div className="bg-navy-900 rounded-lg overflow-hidden relative" style={{ aspectRatio: '2/1' }}>
                {/* Simulated sonar background */}
                <div className="absolute inset-0 sonar-grid-bg opacity-30" />
                <div className="absolute inset-0 bg-gradient-to-r from-navy-950 via-navy-900 to-navy-950" />
                {/* Sonar-like texture */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 512 256" preserveAspectRatio="none">
                  <defs>
                    <filter id="noise">
                      <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
                      <feColorMatrix type="saturate" values="0" />
                    </filter>
                  </defs>
                  <rect width="512" height="256" filter="url(#noise)" opacity="0.4" fill="white" />
                  {/* Nadir dark band */}
                  <rect x="236" y="0" width="40" height="256" fill="#060c18" opacity="0.9" />
                  {/* Bright target */}
                  {detection.bbox_x != null && (
                    <>
                      <rect
                        x={detection.bbox_x} y={detection.bbox_y ?? 0}
                        width={detection.bbox_w ?? 40} height={detection.bbox_h ?? 25}
                        fill="none" stroke="#00B4D8" strokeWidth="2"
                      />
                      <ellipse
                        cx={(detection.bbox_x ?? 0) + (detection.bbox_w ?? 40) / 2}
                        cy={(detection.bbox_y ?? 0) + (detection.bbox_h ?? 25) / 2}
                        rx={detection.bbox_w ? detection.bbox_w / 2 : 20}
                        ry={detection.bbox_h ? detection.bbox_h / 2 : 12}
                        fill="white" opacity="0.6"
                      />
                      {/* Shadow */}
                      <rect
                        x={(detection.bbox_x ?? 0) + (detection.bbox_w ?? 40)}
                        y={detection.bbox_y ?? 0}
                        width={(detection.bbox_w ?? 40) * 1.5}
                        height={detection.bbox_h ?? 25}
                        fill="#000" opacity="0.7"
                      />
                    </>
                  )}
                </svg>
                <div className="absolute bottom-2 left-2 text-xs font-mono text-sonar-cyan/70">
                  SONAR-X · {detection.inference_mode}
                </div>
                {detection.data_source === 'DEMO' && (
                  <div className="absolute top-2 right-2 text-xs font-bold text-amber-400 bg-black/50 px-2 py-0.5 rounded">
                    DEMO/SYNTHETIC
                  </div>
                )}
              </div>
              {detection.bbox_x != null && (
                <p className="text-xs text-slate-400 mt-2">
                  Bounding box: ({detection.bbox_x}, {detection.bbox_y}) {detection.bbox_w}×{detection.bbox_h} px
                </p>
              )}
            </CardBody>
          </Card>

          {/* Processing provenance */}
          <Card>
            <CardHeader><CardTitle>Processing Provenance</CardTitle></CardHeader>
            <CardBody className="space-y-2">
              {Object.entries(detection.processing_summary ?? {}).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 capitalize">{k.replace('_', ' ')}</span>
                  <StepStatusChip status={String(v)} />
                </div>
              ))}
              <div className="pt-2 border-t border-slate-100">
                <p className="text-xs text-slate-400">Inference: {detection.inference_mode}</p>
                {detection.inference_mode === 'CLASSICAL_CV' && (
                  <p className="text-xs text-amber-600 mt-1">Classical CV fallback — not a trained model.</p>
                )}
              </div>
            </CardBody>
          </Card>

          {/* Location */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-slate-400" />
                <CardTitle>Location</CardTitle>
              </div>
            </CardHeader>
            <CardBody>
              {detection.latitude != null ? (
                <div className="space-y-1.5">
                  <p className="font-mono text-sm text-navy-900">
                    {detection.latitude.toFixed(5)}°N, {detection.longitude?.toFixed(5)}°E
                  </p>
                  <p className="text-xs text-slate-400">WGS84 · {detection.coordinate_note || 'Survey metadata'}</p>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-slate-400">
                  <AlertTriangle className="w-4 h-4" />
                  <p className="text-sm">Geolocation metadata unavailable.</p>
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* RIGHT: Classification + evidence */}
        <div className="col-span-3 space-y-4">
          {/* Classification summary */}
          <Card>
            <CardBody>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Classification</p>
                  <ClassBadge c={detection.classification} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Confidence*</p>
                  <p className="text-2xl font-bold text-navy-900">{detection.confidence?.toFixed(0)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Evidence*</p>
                  <p className="text-2xl font-bold text-navy-900">{detection.evidence_score?.toFixed(0)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">FP Risk</p>
                  <RiskBadge risk={detection.false_positive_risk} />
                </div>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <HazardBadge level={detection.hazard_level} />
                <VerificationBadge status={detection.verification_status} />
                {detection.temporal_status && (
                  <span className="text-xs bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded font-semibold">
                    {detection.temporal_status.replace('_', ' ')}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2">
                * Prototype scores — not scientifically validated probabilities.
              </p>
            </CardBody>
          </Card>

          {/* Hazard */}
          {detection.hazard_level !== 'NONE' && (
            <HazardPanel
              level={detection.hazard_level}
              score={detection.hazard_score}
              indicators={detection.hazard_indicators}
              limitedData={detection.hazard_limited_data}
              recommendedAction={detection.recommended_action}
            />
          )}

          {/* Fingerprint */}
          {fp && (
            <Card>
              <CardHeader>
                <CardTitle>Sonar Fingerprint</CardTitle>
                <p className="text-xs text-slate-400 mt-0.5">Seven-cue acoustic evidence analysis</p>
              </CardHeader>
              <CardBody>
                <FingerprintRadar fingerprint={fp} />
              </CardBody>
            </Card>
          )}

          {/* Evidence fusion */}
          {fp && (
            <Card>
              <CardHeader>
                <CardTitle>Evidence Fusion</CardTitle>
                <p className="text-xs text-slate-400 mt-0.5">Weighted multi-cue evidence integration</p>
              </CardHeader>
              <CardBody>
                <EvidenceBar
                  fingerprint={fp}
                  evidenceScore={detection.evidence_score}
                  fpRisk={detection.false_positive_risk}
                />
              </CardBody>
            </Card>
          )}

          {/* Explainability */}
          <Card>
            <CardHeader>
              <CardTitle>Why SONAR-X Reached This Decision</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              {detection.supporting_evidence?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-2">Supporting Evidence</p>
                  <ul className="space-y-1.5">
                    {detection.supporting_evidence.map((e, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <span className="text-emerald-500 mt-0.5 shrink-0">+</span>
                        {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {detection.counter_evidence?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">Counter-Evidence</p>
                  <ul className="space-y-1.5">
                    {detection.counter_evidence.map((e, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                        <span className="text-amber-500 mt-0.5 shrink-0">−</span>
                        {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {detection.classification === 'UNKNOWN_ANOMALY' && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm text-orange-700">
                  <strong>UNKNOWN ANOMALY</strong> is a valid classification. Insufficient evidence to confidently assign
                  a definitive class. Human review recommended.
                </div>
              )}
            </CardBody>
          </Card>

          {/* Verification history */}
          {detection.verifications && detection.verifications.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Verification History</CardTitle></CardHeader>
              <CardBody>
                <div className="divide-y divide-slate-50">
                  {detection.verifications.map(v => (
                    <div key={v.id} className="py-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-navy-900">{v.decision}</span>
                        <span className="text-xs text-slate-400">{new Date(v.timestamp).toLocaleString()}</span>
                      </div>
                      <p className="text-xs text-slate-500">{v.reviewer_email}</p>
                      {v.comment && <p className="text-sm text-slate-600 mt-1 italic">"{v.comment}"</p>}
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <Link to={`/detections/${id}/verify`}
              className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              <CheckCircle className="w-4 h-4" /> Verify / Review
            </Link>
            <Link to={`/detections/${id}/verify`}
              className="flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 px-4 py-2 rounded-lg text-sm transition-colors">
              <Clock className="w-4 h-4" /> View History
            </Link>
            {detection.debris_uid && (
              <Link to={`/temporal`}
                className="flex items-center gap-2 border border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100 px-4 py-2 rounded-lg text-sm transition-colors">
                <GitBranch className="w-4 h-4" /> Temporal Analysis
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
