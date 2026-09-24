import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Activity, AlertTriangle, CheckCircle, Clock, Database,
  Eye, Map, PlusCircle, Radio, BarChart3, ArrowRight, Shield
} from 'lucide-react'
import { surveysAPI, detectionsAPI } from '../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../components/ui/Card'
import { ClassBadge, HazardBadge, DemoBadge } from '../components/ui/StatusChip'
import { PageLoader } from '../components/ui/LoadingSpinner'
import type { DashboardStats, Survey, Detection } from '../types'

const ENGINES = [
  'Preprocessing Engine',
  'Detection Engine',
  'Fingerprint Engine',
  'Evidence Fusion',
  'Hazard Engine',
  'Temporal Engine',
  'Reporting Engine',
]

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [surveys, setSurveys] = useState<Survey[]>([])
  const [detections, setDetections] = useState<Detection[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      surveysAPI.stats(),
      surveysAPI.list(),
      detectionsAPI.list({ page_size: 6 }),
    ]).then(([s, sv, d]) => {
      setStats(s.data as DashboardStats)
      setSurveys((sv.data as { results?: Survey[] }).results ?? (sv.data as Survey[]))
      setDetections((d.data as { results?: Detection[] }).results ?? (d.data as Detection[]))
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <PageLoader text="Loading SONAR-X dashboard…" />

  const statCards = [
    { label: 'Total Surveys', value: stats?.total_surveys ?? 0, icon: Database, color: 'text-ocean-600' },
    { label: 'Detections', value: stats?.total_detections ?? 0, icon: Radio, color: 'text-sonar-cyan' },
    { label: 'Marine Debris', value: stats?.marine_debris ?? 0, icon: Activity, color: 'text-blue-600' },
    { label: 'Natural Formations', value: stats?.natural_formation ?? 0, icon: Map, color: 'text-emerald-600' },
    { label: 'Sonar Artifacts', value: stats?.sonar_artifact ?? 0, icon: Eye, color: 'text-purple-600' },
    { label: 'Unknown Anomalies', value: stats?.unknown_anomaly ?? 0, icon: AlertTriangle, color: 'text-orange-500' },
    { label: 'Hazard Flags', value: stats?.hazard_flags ?? 0, icon: Shield, color: 'text-red-600' },
    { label: 'Pending Verification', value: stats?.pending_verification ?? 0, icon: Clock, color: 'text-amber-600' },
  ]

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 rounded-lg bg-ocean-600/10 border border-ocean-600/20 flex items-center justify-center">
              <Radio className="w-4 h-4 text-ocean-600" />
            </div>
            <h1 className="text-2xl font-bold text-navy-900">SONAR-X</h1>
          </div>
          <p className="text-slate-500 text-sm">Physics-Aware Explainable Marine Debris Intelligence System</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Upload Sonar Data
          </button>
          <Link
            to="/evaluation"
            className="flex items-center gap-2 border border-slate-200 hover:border-slate-300 bg-white text-slate-600 hover:text-slate-800 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <BarChart3 className="w-4 h-4" />
            Evaluation
          </Link>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardBody className="py-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-slate-50 ${color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-navy-900">{value}</p>
                  <p className="text-xs text-slate-500 leading-tight">{label}</p>
                </div>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Recent surveys */}
        <div className="col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Surveys</CardTitle>
                <Link to="/surveys/new" className="text-xs text-ocean-600 hover:underline flex items-center gap-1">
                  New <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardHeader>
            <CardBody className="p-0">
              {surveys.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-sm">
                  No surveys yet. Start by creating a new survey or opening the demo.
                </div>
              ) : (
                <div className="divide-y divide-slate-50">
                  {surveys.slice(0, 6).map(s => (
                    <Link
                      key={s.id}
                      to={`/surveys/${s.id}`}
                      className="flex items-center justify-between px-6 py-3.5 hover:bg-slate-50 transition-colors"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-navy-900 text-sm truncate">{s.name}</span>
                          {s.is_demo && <DemoBadge />}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 font-mono">{s.survey_id} · {s.date}</p>
                      </div>
                      <div className="flex items-center gap-3 shrink-0 ml-4">
                        <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                          {s.detection_count} detections
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                          s.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700' :
                          s.status === 'FAILED' ? 'bg-red-50 text-red-700' :
                          'bg-amber-50 text-amber-700'
                        }`}>
                          {s.status}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
              {/* Demo shortcut */}
              {surveys.filter(s => s.is_demo).length === 0 && (
                <div className="px-6 py-4 bg-amber-50/50 border-t border-amber-100">
                  <p className="text-xs text-amber-700 mb-2 font-medium">No demo survey found. Seed demo data first.</p>
                  <code className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded">
                    python manage.py seed_demo
                  </code>
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* System status */}
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>System Status</CardTitle></CardHeader>
            <CardBody className="space-y-2.5">
              {ENGINES.map(name => (
                <div key={name} className="flex items-center justify-between">
                  <span className="text-xs text-slate-600">{name}</span>
                  <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-700">
                    <CheckCircle className="w-3 h-3" /> READY
                  </span>
                </div>
              ))}
            </CardBody>
          </Card>

          {/* Quick actions */}
          <Card>
            <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
            <CardBody className="space-y-2">
              <Link
                to="/upload"
                className="flex items-center gap-2 w-full text-sm text-ocean-600 hover:text-ocean-700 hover:bg-ocean-50 px-3 py-2 rounded-lg transition-colors"
              >
                <PlusCircle className="w-4 h-4" />
                Upload Sonar Data
              </Link>
              {surveys.filter(s => s.is_demo)[0] && (
                <Link
                  to={`/surveys/${surveys.filter(s => s.is_demo)[0].id}`}
                  className="flex items-center gap-2 w-full text-sm text-amber-600 hover:text-amber-700 hover:bg-amber-50 px-3 py-2 rounded-lg transition-colors"
                >
                  <Radio className="w-4 h-4" />
                  Open Demo Survey
                </Link>
              )}
              <Link
                to="/temporal"
                className="flex items-center gap-2 w-full text-sm text-slate-600 hover:text-slate-800 hover:bg-slate-50 px-3 py-2 rounded-lg transition-colors"
              >
                <Clock className="w-4 h-4" />
                Temporal Intelligence
              </Link>
              <Link
                to="/evaluation"
                className="flex items-center gap-2 w-full text-sm text-slate-600 hover:text-slate-800 hover:bg-slate-50 px-3 py-2 rounded-lg transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                Evaluation Metrics
              </Link>
            </CardBody>
          </Card>
        </div>
      </div>

      {/* Recent detections */}
      {detections.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Detections</CardTitle>
              <span className="text-xs text-slate-400">Showing latest 6</span>
            </div>
          </CardHeader>
          <CardBody className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    {['Detection UID', 'Classification', 'Conf.*', 'Hazard', 'Verification', 'Survey', 'Source'].map(h => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {detections.map(det => (
                    <tr key={det.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <Link to={`/detections/${det.id}`} className="text-ocean-600 hover:underline font-mono text-xs">
                          {det.detection_uid}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <ClassBadge c={det.classification} />
                      </td>
                      <td className="px-4 py-3 text-slate-700">{det.confidence?.toFixed(0)}</td>
                      <td className="px-4 py-3"><HazardBadge level={det.hazard_level} /></td>
                      <td className="px-4 py-3 text-xs text-slate-500">{det.verification_status}</td>
                      <td className="px-4 py-3 text-xs text-slate-500 font-mono">{det.survey_id}</td>
                      <td className="px-4 py-3">
                        {det.data_source === 'DEMO' && <DemoBadge />}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 border-t border-slate-50">
              <p className="text-xs text-slate-400">* Confidence is a prototype evidence score, NOT a validated probability.</p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
