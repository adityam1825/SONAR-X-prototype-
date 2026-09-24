import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Download, FileJson, FileText, Table, AlertTriangle } from 'lucide-react'
import { exportsAPI, downloadBlob } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'

interface ExportSummary {
  survey_id: string
  total_detections: number
  geolocated: number
  no_coordinates: number
  by_class: Record<string, number>
  by_hazard: Record<string, number>
  data_source: string
}

export default function ExportPage() {
  const { id } = useParams<{ id: string }>()
  const [summary, setSummary] = useState<ExportSummary | null>(null)
  const [loadingSummary, setLoadingSummary] = useState(true)
  const [exporting, setExporting] = useState<string | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!id) return
    exportsAPI.summary(id)
      .then(r => setSummary(r.data as ExportSummary))
      .catch(() => setSummary(null))
      .finally(() => setLoadingSummary(false))
  }, [id])

  const doExport = async (fmt: 'geojson' | 'kml' | 'csv') => {
    setExporting(fmt); setMessage('')
    try {
      const fnMap = { geojson: exportsAPI.geojson, kml: exportsAPI.kml, csv: exportsAPI.csv }
      const extMap = { geojson: 'geojson', kml: 'kml', csv: 'csv' }
      const resp = await fnMap[fmt](id!)
      downloadBlob(resp.data as Blob, `sonarx_${summary?.survey_id ?? id}.${extMap[fmt]}`)
      setMessage(`${fmt.toUpperCase()} exported successfully.`)
    } catch {
      setMessage(`Export failed. Please try again.`)
    } finally { setExporting(null) }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        title="Export Results"
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Export' }]}
      />

      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-start gap-2 text-sm text-amber-700">
        <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
        <span>
          AI-generated observations require human verification before operational use.
          Exports include data source labelling. Demo exports are clearly marked DATA SOURCE: DEMO.
        </span>
      </div>

      {/* Summary */}
      {!loadingSummary && summary && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Export Summary</CardTitle>
              {summary.data_source === 'DEMO' && (
                <span className="text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">
                  DATA SOURCE: DEMO
                </span>
              )}
            </div>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center bg-slate-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-navy-900">{summary.total_detections}</p>
                <p className="text-xs text-slate-500">Total Detections</p>
              </div>
              <div className="text-center bg-emerald-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-emerald-700">{summary.geolocated}</p>
                <p className="text-xs text-slate-500">Geolocated</p>
              </div>
              <div className="text-center bg-amber-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-amber-700">{summary.no_coordinates}</p>
                <p className="text-xs text-slate-500">No GPS Coords</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">By Class</p>
                {Object.entries(summary.by_class).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1">
                    <span className="text-slate-600">{k.replace('_', ' ')}</span>
                    <span className="font-semibold">{v}</span>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">By Hazard</p>
                {Object.entries(summary.by_hazard).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1">
                    <span className="text-slate-600">{k.replace('_', ' ')}</span>
                    <span className="font-semibold">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Export buttons */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            fmt: 'geojson' as const,
            icon: FileJson,
            label: 'GeoJSON',
            desc: 'RFC 7946 · WGS84 · Point features with properties',
            color: 'border-ocean-200 bg-ocean-50 hover:bg-ocean-100',
            textColor: 'text-ocean-700',
          },
          {
            fmt: 'kml' as const,
            icon: FileText,
            label: 'KML',
            desc: 'Google Earth · Placemarks with styles by hazard level',
            color: 'border-emerald-200 bg-emerald-50 hover:bg-emerald-100',
            textColor: 'text-emerald-700',
          },
          {
            fmt: 'csv' as const,
            icon: Table,
            label: 'CSV',
            desc: 'All detections · Empty coords if unavailable',
            color: 'border-purple-200 bg-purple-50 hover:bg-purple-100',
            textColor: 'text-purple-700',
          },
        ].map(({ fmt, icon: Icon, label, desc, color, textColor }) => (
          <button
            key={fmt}
            onClick={() => doExport(fmt)}
            disabled={exporting !== null}
            className={`flex flex-col items-center gap-3 border-2 rounded-xl p-6 transition-all disabled:opacity-60 ${color}`}
          >
            <Icon className={`w-8 h-8 ${textColor}`} />
            <div className="text-center">
              <p className={`font-bold text-base ${textColor}`}>{label}</p>
              <p className="text-xs text-slate-500 mt-1">{desc}</p>
            </div>
            <div className={`flex items-center gap-1.5 text-sm font-medium ${textColor}`}>
              <Download className="w-4 h-4" />
              {exporting === fmt ? 'Exporting…' : `Download ${label}`}
            </div>
          </button>
        ))}
      </div>

      {message && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-emerald-700 text-sm">
          {message}
        </div>
      )}

      <Card>
        <CardBody>
          <p className="text-xs text-slate-500">
            <strong>Export notes:</strong> GeoJSON and KML include only geolocated detections.
            CSV includes all detections with empty latitude/longitude fields where GPS unavailable.
            All exports include data source label, software version, survey ID, generation timestamp, and disclaimer.
            GPS coordinates are never fabricated — only metadata-derived positions are included.
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
