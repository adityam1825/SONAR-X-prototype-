import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Play, ArrowRight, Info, CheckCircle } from 'lucide-react'
import { sonarAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import { StepStatusChip } from '../../components/ui/StatusChip'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface ProcessingResult {
  nadir: { status: string; reason: string; start_px: number; end_px: number; width_px: number }
  gain: { status: string; reason: string }
  slant_range: { status: string; reason: string; pixel_scale_gpp: number | null }
  noise: { status: string }
  contrast: { status: string }
  quality: { status: string; score: number; level: string; saturation_ratio: number; dropout_ratio: number; snr_proxy: number; image_contrast: number; usable_area_ratio: number; flags: string[] }
}

const STEPS = [
  { key: 'nadir', label: 'Nadir Gap Handling', num: '01' },
  { key: 'gain', label: 'Gain Correction', num: '02' },
  { key: 'slant_range', label: 'Slant-Range Correction', num: '03' },
  { key: 'noise', label: 'Noise Reduction', num: '04' },
  { key: 'contrast', label: 'Contrast Enhancement', num: '05' },
  { key: 'quality', label: 'Quality Assessment', num: '06' },
]

export default function PreprocessingPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [fileId, setFileId] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [origImg, setOrigImg] = useState<string | null>(null)
  const [procImg, setProcImg] = useState<string | null>(null)
  const [profile, setProfile] = useState<number[] | null>(null)
  const [quality, setQuality] = useState<{ score: number; level: string; flags: string[] } | null>(null)
  const [error, setError] = useState('')
  const [sliderPos, setSliderPos] = useState(50)

  const run = async () => {
    if (!fileId.trim()) { setError('Enter a file ID.'); return }
    setRunning(true); setError('')
    try {
      const resp = await sonarAPI.preprocess(fileId)
      const d = resp.data as {
        processing_result: ProcessingResult
        original_image_b64: string
        processed_image_b64: string
        across_track_profile: number[]
        quality: { score: number; level: string; flags: string[] }
      }
      setResult(d.processing_result)
      setOrigImg(`data:image/png;base64,${d.original_image_b64}`)
      setProcImg(`data:image/png;base64,${d.processed_image_b64}`)
      setProfile(d.across_track_profile)
      setQuality(d.quality)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Preprocessing failed.')
    } finally { setRunning(false) }
  }

  const profileData = profile?.map((v, i) => ({ x: i, intensity: v })) ?? []

  const qScore = quality?.score ?? result?.quality?.score ?? 0
  const qLevel = quality?.level ?? result?.quality?.level ?? 'UNKNOWN'
  const qColor = qLevel === 'GOOD' ? 'text-emerald-700' : qLevel === 'MODERATE' ? 'text-amber-700' : 'text-red-700'

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <PageHeader
        title="Sonar Preprocessing"
        subtitle="Nadir handling · Gain correction · Slant-range · Noise reduction · Contrast · Quality"
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Preprocessing' }]}
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 flex items-start gap-2 text-sm text-blue-700">
        <Info className="w-4 h-4 mt-0.5 shrink-0" />
        <span>
          The original image is never modified. Preprocessing creates a processed derivative.
          Slant-range correction requires altitude + range scale metadata — missing values are handled gracefully.
        </span>
      </div>

      {/* File input */}
      <Card>
        <CardHeader><CardTitle>Run Preprocessing Pipeline</CardTitle></CardHeader>
        <CardBody className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-slate-600 mb-1">File ID (UUID)</label>
            <input
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-ocean-500"
              value={fileId} onChange={e => setFileId(e.target.value)}
              placeholder="Enter file UUID…"
            />
          </div>
          <button
            onClick={run} disabled={running}
            className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Play className="w-4 h-4" />
            {running ? 'Processing…' : 'Run Preprocessing'}
          </button>
        </CardBody>
      </Card>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">{error}</div>}

      {running && <PageLoader text="Running preprocessing pipeline…" />}

      {result && !running && (
        <>
          {/* Pipeline steps */}
          <Card>
            <CardHeader><CardTitle>Processing Pipeline Status</CardTitle></CardHeader>
            <CardBody>
              <div className="grid grid-cols-3 gap-3">
                {STEPS.map(({ key, label, num }) => {
                  const step = result[key as keyof ProcessingResult] as { status: string; reason?: string }
                  return (
                    <div key={key} className="flex items-start gap-3 border border-slate-100 rounded-lg p-3">
                      <span className="text-xs font-mono text-slate-300 mt-0.5 w-5 shrink-0">{num}</span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold text-slate-700">{label}</span>
                          <StepStatusChip status={step?.status ?? 'SKIPPED'} />
                        </div>
                        {step?.reason && (
                          <p className="text-xs text-slate-400 leading-tight">{step.reason}</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardBody>
          </Card>

          {/* Before/After images */}
          {origImg && procImg && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Before / After Comparison</CardTitle>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span>Slider: {sliderPos}%</span>
                  </div>
                </div>
              </CardHeader>
              <CardBody>
                {/* Slider comparison */}
                <div className="relative overflow-hidden rounded-lg border border-slate-200" style={{ height: 220 }}>
                  {/* Processed (full width, behind) */}
                  <img src={procImg} alt="Processed" className="absolute inset-0 w-full h-full object-cover"
                    style={{ imageRendering: 'pixelated' }} />
                  {/* Original (clipped) */}
                  <div className="absolute inset-0 overflow-hidden" style={{ width: `${sliderPos}%` }}>
                    <img src={origImg} alt="Original" className="w-full h-full object-cover"
                      style={{ width: `${100 / sliderPos * 100}%`, imageRendering: 'pixelated' }} />
                  </div>
                  {/* Divider */}
                  <div className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg cursor-ew-resize"
                    style={{ left: `${sliderPos}%` }} />
                  {/* Labels */}
                  <div className="absolute top-2 left-2 text-xs font-bold text-white bg-black/50 px-2 py-0.5 rounded">ORIGINAL</div>
                  <div className="absolute top-2 right-2 text-xs font-bold text-white bg-ocean-600/80 px-2 py-0.5 rounded">PROCESSED</div>
                </div>
                <input
                  type="range" min={5} max={95} value={sliderPos}
                  onChange={e => setSliderPos(Number(e.target.value))}
                  className="w-full mt-2 accent-ocean-600"
                />
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <p className="text-xs font-medium text-slate-500 mb-1">ORIGINAL</p>
                    <img src={origImg} alt="Original" className="w-full rounded border border-slate-200"
                      style={{ imageRendering: 'pixelated' }} />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500 mb-1">PROCESSED</p>
                    <img src={procImg} alt="Processed" className="w-full rounded border border-ocean-200"
                      style={{ imageRendering: 'pixelated' }} />
                  </div>
                </div>
              </CardBody>
            </Card>
          )}

          {/* Intensity profile */}
          {profileData.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Across-Track Intensity Profile</CardTitle></CardHeader>
              <CardBody>
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={profileData} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                      <XAxis dataKey="x" tick={{ fontSize: 9 }} label={{ value: 'Column (px)', position: 'insideBottom', fontSize: 10 }} />
                      <YAxis domain={[0, 255]} tick={{ fontSize: 9 }} />
                      <Tooltip formatter={(v: number) => [v.toFixed(1), 'Mean Intensity']} contentStyle={{ fontSize: 11 }} />
                      <Line type="monotone" dataKey="intensity" stroke="#0077B6" dot={false} strokeWidth={1.5} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Dark nadir region visible at image centre. Gain correction normalises the across-track intensity gradient.
                </p>
              </CardBody>
            </Card>
          )}

          {/* Quality */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Quality Assessment</CardTitle></CardHeader>
              <CardBody>
                <div className="flex items-center gap-4 mb-4">
                  <div>
                    <p className="text-4xl font-bold text-navy-900">{qScore.toFixed(0)}</p>
                    <p className="text-xs text-slate-400">/ 100</p>
                  </div>
                  <div>
                    <p className={`text-xl font-bold ${qColor}`}>{qLevel}</p>
                    {(quality?.flags ?? []).map(f => (
                      <span key={f} className="text-xs bg-amber-50 text-amber-700 border border-amber-200 rounded px-1.5 py-0.5 mr-1">{f}</span>
                    ))}
                  </div>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-3">
                  <div className="h-full bg-ocean-600 rounded-full" style={{ width: `${qScore}%` }} />
                </div>
                {result.quality && (
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                    {[
                      ['Saturation', `${(result.quality.saturation_ratio * 100).toFixed(1)}%`],
                      ['Dropouts', `${(result.quality.dropout_ratio * 100).toFixed(1)}%`],
                      ['SNR Proxy', result.quality.snr_proxy?.toFixed(1)],
                      ['Contrast', result.quality.image_contrast?.toFixed(1)],
                      ['Usable Area', `${(result.quality.usable_area_ratio * 100).toFixed(1)}%`],
                      ['Nadir Width', `${result.nadir?.width_px ?? '—'} px`],
                    ].map(([k, v]) => (
                      <div key={k}><dt className="text-slate-400">{k}</dt><dd className="font-medium text-navy-900">{v}</dd></div>
                    ))}
                  </dl>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader><CardTitle>Processing Provenance</CardTitle></CardHeader>
              <CardBody className="space-y-2.5">
                {STEPS.map(({ key, label }) => {
                  const step = result[key as keyof ProcessingResult] as { status?: string }
                  return (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-xs text-slate-600">{label}</span>
                      <StepStatusChip status={step?.status ?? '—'} />
                    </div>
                  )
                })}
              </CardBody>
            </Card>
          </div>

          {/* Nadir details */}
          {result.nadir && (
            <Card>
              <CardHeader><CardTitle>Nadir Region</CardTitle></CardHeader>
              <CardBody>
                <div className="flex items-start gap-3 text-sm">
                  <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                  <div>
                    <p><strong>Method:</strong> {result.nadir.start_px !== null ? `Columns ${result.nadir.start_px}–${result.nadir.end_px} (${result.nadir.width_px} px wide)` : '—'}</p>
                    <p className="text-slate-500 text-xs mt-1">{result.nadir.reason}</p>
                    <p className="text-xs text-amber-600 mt-1">
                      The nadir region is masked. No seabed information is inferred inside the nadir.
                      Detections inside the nadir region are suppressed.
                    </p>
                  </div>
                </div>
              </CardBody>
            </Card>
          )}

          <div className="flex justify-end">
            <button
              onClick={() => navigate(`/surveys/${id}/analysis`)}
              className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Continue to Analysis <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </>
      )}
    </div>
  )
}
