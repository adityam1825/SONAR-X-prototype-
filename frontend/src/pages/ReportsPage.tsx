import { useEffect, useState } from 'react'
import { FileText, Download, Loader } from 'lucide-react'
import { surveysAPI, reportsAPI, downloadBlob } from '../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'
import type { Survey } from '../types'

export default function ReportsPage() {
  const [surveys, setSurveys] = useState<Survey[]>([])
  const [generating, setGenerating] = useState<string | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    surveysAPI.list().then(r => {
      const d = r.data as { results?: Survey[] } | Survey[]
      setSurveys(Array.isArray(d) ? d : d.results ?? [])
    }).catch(console.error)
  }, [])

  const generateSurveyReport = async (surveyId: string, surveyName: string) => {
    setGenerating(surveyId); setMessage('')
    try {
      const resp = await reportsAPI.generateSurvey(surveyId)
      const d = resp.data as { report_id: string; download_url: string }
      setMessage(`Report generated for ${surveyName}. Downloading…`)
      // Attempt download
      const dlResp = await reportsAPI.download(d.report_id)
      downloadBlob(dlResp.data as Blob, `sonarx_survey_report_${surveyId}.pdf`)
    } catch (e: unknown) {
      setMessage((e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Report generation failed.')
    } finally { setGenerating(null) }
  }

  const generateTemporalReport = async (debrisUid: string) => {
    setGenerating(debrisUid); setMessage('')
    try {
      const resp = await reportsAPI.generateTemporal(debrisUid)
      const d = resp.data as { report_id: string }
      setMessage(`Temporal report generated for ${debrisUid}. Downloading…`)
      const dlResp = await reportsAPI.download(d.report_id)
      downloadBlob(dlResp.data as Blob, `sonarx_temporal_report_${debrisUid}.pdf`)
    } catch (e: unknown) {
      setMessage((e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Report generation failed.')
    } finally { setGenerating(null) }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Generate PDF survey and temporal intelligence reports"
        breadcrumbs={[{ label: 'Reports' }]}
      />

      {message && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-emerald-700 text-sm">
          {message}
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>Survey Reports</CardTitle></CardHeader>
        <CardBody className="p-0">
          {surveys.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-sm">No surveys available.</div>
          ) : (
            <div className="divide-y divide-slate-50">
              {surveys.map(s => (
                <div key={s.id} className="flex items-center justify-between px-6 py-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-navy-900 text-sm">{s.name}</span>
                      {s.is_demo && <span className="text-xs font-bold text-amber-600 bg-amber-50 border border-amber-200 px-1.5 rounded">DEMO</span>}
                    </div>
                    <p className="text-xs text-slate-400 font-mono">{s.survey_id} · {s.date}</p>
                  </div>
                  <button
                    onClick={() => generateSurveyReport(s.id, s.name)}
                    disabled={generating === s.id}
                    className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    {generating === s.id
                      ? <><Loader className="w-4 h-4 animate-spin" /> Generating…</>
                      : <><FileText className="w-4 h-4" /> Generate PDF</>
                    }
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Temporal Reports</CardTitle></CardHeader>
        <CardBody>
          <p className="text-sm text-slate-500 mb-4">Generate temporal intelligence reports for tracked debris objects.</p>
          <div className="grid grid-cols-2 gap-3">
            {['SX-DB-0001', 'SX-DB-0002', 'SX-DB-0003', 'SX-DB-0004', 'SX-DB-0005'].map(uid => (
              <button
                key={uid}
                onClick={() => generateTemporalReport(uid)}
                disabled={generating === uid}
                className="flex items-center justify-between border border-slate-200 rounded-lg px-4 py-3 hover:bg-slate-50 transition-colors text-sm"
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <span className="font-mono text-slate-700">{uid}</span>
                </div>
                {generating === uid ? (
                  <Loader className="w-4 h-4 animate-spin text-ocean-600" />
                ) : (
                  <Download className="w-4 h-4 text-slate-400" />
                )}
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-3">
            Reports include survey timelines, fingerprint similarity scores, temporal status, and verification decisions.
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <p className="text-xs text-slate-500">
            All generated reports include: DATA SOURCE label, processing provenance, prototype disclaimers,
            and "AI-generated observations require verification" footer.
            Reports are generated using ReportLab and stored in the media directory.
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
