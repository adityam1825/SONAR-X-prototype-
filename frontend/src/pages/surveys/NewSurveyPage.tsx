import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlusCircle, AlertCircle } from 'lucide-react'
import { surveysAPI } from '../../services/api'
import PageHeader from '../../components/ui/PageHeader'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'

export default function NewSurveyPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    name: '',
    date: new Date().toISOString().split('T')[0],
    area: '',
    operator: '',
    data_source: 'SURVEY',
    altitude_m: '',
    range_scale_mpp: '',
    channel_layout: 'BOTH',
    already_gain_corrected: false,
    already_slant_range_corrected: false,
    already_processed: false,
    latitude: '',
    longitude: '',
    notes: '',
  })

  const set = (k: string, v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = {
        ...form,
        altitude_m: form.altitude_m ? parseFloat(form.altitude_m) : null,
        range_scale_mpp: form.range_scale_mpp ? parseFloat(form.range_scale_mpp) : null,
        latitude: form.latitude ? parseFloat(form.latitude) : null,
        longitude: form.longitude ? parseFloat(form.longitude) : null,
        is_demo: form.data_source === 'DEMO',
      }
      const resp = await surveysAPI.create(payload)
      const survey = resp.data as { id: string }
      navigate(`/surveys/${survey.id}`)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: Record<string, string[]> } })?.response?.data
      setError(msg ? Object.values(msg).flat().join(' ') : 'Failed to create survey.')
    } finally {
      setLoading(false)
    }
  }

  const inputClass = 'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ocean-500 focus:ring-1 focus:ring-ocean-200 transition-all'
  const labelClass = 'block text-xs font-semibold text-slate-600 mb-1'
  const checkClass = 'w-4 h-4 rounded border-slate-300 text-ocean-600 focus:ring-ocean-500'

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        title="Create New Survey"
        subtitle="Configure sonar metadata before uploading imagery"
        breadcrumbs={[{ label: 'New Survey' }]}
      />

      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        <Card>
          <CardHeader><CardTitle>Survey Information</CardTitle></CardHeader>
          <CardBody className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className={labelClass}>Survey Name *</label>
              <input className={inputClass} value={form.name} onChange={e => set('name', e.target.value)} required placeholder="e.g. Arabian Sea Survey 2024" />
            </div>
            <div>
              <label className={labelClass}>Survey Date *</label>
              <input type="date" className={inputClass} value={form.date} onChange={e => set('date', e.target.value)} required />
            </div>
            <div>
              <label className={labelClass}>Data Source *</label>
              <select className={inputClass} value={form.data_source} onChange={e => set('data_source', e.target.value)}>
                <option value="SURVEY">SURVEY — Real data</option>
                <option value="DEMO">DEMO — Demonstration data</option>
              </select>
              {form.data_source === 'DEMO' && (
                <p className="text-xs text-amber-600 mt-1">⚠ Demo results will be labelled DATA SOURCE: DEMO</p>
              )}
            </div>
            <div>
              <label className={labelClass}>Survey Area</label>
              <input className={inputClass} value={form.area} onChange={e => set('area', e.target.value)} placeholder="e.g. Arabian Sea — Western Coast" />
            </div>
            <div>
              <label className={labelClass}>Operator / Team</label>
              <input className={inputClass} value={form.operator} onChange={e => set('operator', e.target.value)} placeholder="e.g. Team Kurukshetra" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sonar Metadata</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">
              Altitude and range scale are required for slant-range correction. Missing values will be handled gracefully.
            </p>
          </CardHeader>
          <CardBody className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Altitude above seabed (m)</label>
              <input type="number" step="0.1" className={inputClass} value={form.altitude_m}
                onChange={e => set('altitude_m', e.target.value)} placeholder="e.g. 2.5" />
              <p className="text-xs text-slate-400 mt-1">Leave blank if unavailable — slant-range correction will be skipped.</p>
            </div>
            <div>
              <label className={labelClass}>Slant-range scale (m/px)</label>
              <input type="number" step="0.001" className={inputClass} value={form.range_scale_mpp}
                onChange={e => set('range_scale_mpp', e.target.value)} placeholder="e.g. 0.2" />
            </div>
            <div>
              <label className={labelClass}>Channel Layout</label>
              <select className={inputClass} value={form.channel_layout} onChange={e => set('channel_layout', e.target.value)}>
                <option value="BOTH">Both (Port + Starboard)</option>
                <option value="PORT">Port only</option>
                <option value="STARBOARD">Starboard only</option>
              </select>
            </div>
            <div className="space-y-3">
              {[
                { key: 'already_gain_corrected', label: 'Already gain corrected?' },
                { key: 'already_slant_range_corrected', label: 'Already slant-range corrected?' },
                { key: 'already_processed', label: 'Already processed?' },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className={checkClass}
                    checked={form[key as keyof typeof form] as boolean}
                    onChange={e => set(key, e.target.checked)} />
                  <span className="text-sm text-slate-600">{label}</span>
                </label>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader><CardTitle>Location (optional)</CardTitle></CardHeader>
          <CardBody className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Latitude (WGS84)</label>
              <input type="number" step="0.0001" className={inputClass} value={form.latitude}
                onChange={e => set('latitude', e.target.value)} placeholder="e.g. 19.4521" />
            </div>
            <div>
              <label className={labelClass}>Longitude (WGS84)</label>
              <input type="number" step="0.0001" className={inputClass} value={form.longitude}
                onChange={e => set('longitude', e.target.value)} placeholder="e.g. 72.8403" />
            </div>
            <div className="col-span-2">
              <label className={labelClass}>Survey Notes</label>
              <textarea className={inputClass} rows={3} value={form.notes}
                onChange={e => set('notes', e.target.value)}
                placeholder="Optional survey notes…" />
            </div>
          </CardBody>
        </Card>

        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate(-1)}
            className="px-6 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
            Cancel
          </button>
          <button type="submit" disabled={loading}
            className="flex items-center gap-2 px-6 py-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white rounded-lg text-sm font-medium transition-colors">
            <PlusCircle className="w-4 h-4" />
            {loading ? 'Creating…' : 'Create Survey'}
          </button>
        </div>
      </form>
    </div>
  )
}
