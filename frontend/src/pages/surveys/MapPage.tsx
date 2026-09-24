import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { AlertTriangle, Download, Filter } from 'lucide-react'
import { detectionsAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import SonarMap from '../../components/map/SonarMap'
import type { Detection } from '../../types'

export default function MapPage() {
  const { id } = useParams<{ id: string }>()
  const [detections, setDetections] = useState<Detection[]>([])
  const [loading, setLoading] = useState(true)
  const [filterHazard, setFilterHazard] = useState('')

  useEffect(() => {
    if (!id) return
    detectionsAPI.list({ survey: id }).then(r => {
      const d = r.data as { results?: Detection[] } | Detection[]
      setDetections(Array.isArray(d) ? d : d.results ?? [])
    }).catch(console.error).finally(() => setLoading(false))
  }, [id])

  if (loading) return <PageLoader text="Loading map…" />

  const geolocated = detections.filter(d => d.latitude != null && d.longitude != null)
  const noCoords = detections.length - geolocated.length
  const filtered = filterHazard ? geolocated.filter(d => d.hazard_level === filterHazard) : geolocated

  const mapCenter: [number, number] = geolocated.length > 0
    ? [geolocated[0].latitude!, geolocated[0].longitude!]
    : [19.45, 72.84]

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <PageHeader
        title="Geospatial Map"
        subtitle={`${geolocated.length} geolocated detections`}
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Map' }]}
        actions={
          <Link to={`/surveys/${id}/export`}
            className="flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 px-4 py-2 rounded-lg text-sm">
            <Download className="w-4 h-4" /> Export
          </Link>
        }
      />

      {noCoords > 0 && (
        <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 text-sm text-amber-700">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {noCoords} detection{noCoords > 1 ? 's' : ''} not shown — geolocation metadata unavailable.
          Coordinates are never fabricated.
        </div>
      )}

      {/* Legend + Filters */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-4 flex-wrap text-xs">
          {[
            { color: '#2563EB', label: 'Marine Debris' },
            { color: '#059669', label: 'Natural Formation' },
            { color: '#7C3AED', label: 'Sonar Artifact' },
            { color: '#EA580C', label: 'Unknown Anomaly' },
            { color: '#D97706', label: 'Caution' },
            { color: '#DC2626', label: 'High Caution' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full border border-white shadow-sm" style={{ background: color }} />
              <span className="text-slate-600">{label}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            className="border border-slate-200 rounded px-2 py-1 text-xs focus:outline-none"
            value={filterHazard} onChange={e => setFilterHazard(e.target.value)}
          >
            <option value="">All Hazard Levels</option>
            <option value="NONE">None</option>
            <option value="CAUTION">Caution</option>
            <option value="HIGH_CAUTION">High Caution</option>
          </select>
        </div>
      </div>

      {/* Map */}
      <Card>
        <CardBody className="p-2">
          {geolocated.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-80 text-slate-400">
              <AlertTriangle className="w-10 h-10 mb-3" />
              <p className="font-medium">No geolocated detections</p>
              <p className="text-sm mt-1">Coordinates unavailable for all detections in this survey.</p>
              <p className="text-xs mt-1 text-slate-300">GPS coordinates are never fabricated.</p>
            </div>
          ) : (
            <div style={{ height: 520 }}>
              <SonarMap detections={filtered} center={mapCenter} zoom={13} />
            </div>
          )}
        </CardBody>
      </Card>

      {/* Detection list below map */}
      <Card>
        <CardHeader>
          <CardTitle>Geolocated Detections ({filtered.length})</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  {['UID', 'Class', 'Latitude', 'Longitude', 'Hazard', 'Source'].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filtered.map(d => (
                  <tr key={d.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-mono text-xs text-ocean-600">{d.detection_uid}</td>
                    <td className="px-4 py-2.5 text-xs">{d.classification.replace('_', ' ')}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">{d.latitude?.toFixed(5)}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">{d.longitude?.toFixed(5)}</td>
                    <td className="px-4 py-2.5 text-xs">{d.hazard_level}</td>
                    <td className="px-4 py-2.5 text-xs text-amber-600">
                      {d.data_source === 'DEMO' ? 'DEMO' : d.data_source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
