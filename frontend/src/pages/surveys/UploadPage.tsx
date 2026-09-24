import { useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Upload, File, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { sonarAPI } from '../../services/api'
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'

const ALLOWED_TYPES = ['.png', '.jpg', '.jpeg', '.tiff', '.tif']
const MAX_MB = 100

export default function UploadPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploaded, setUploaded] = useState<{
    id: string; filename: string; file_size_bytes: number;
    width: number | null; height: number | null; data_source: string
  } | null>(null)
  const [error, setError] = useState('')

  const handleFile = useCallback(async (file: File) => {
    setError('')
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!ext || !ALLOWED_TYPES.includes(`.${ext}`)) {
      setError(`Unsupported file type ".${ext}". Supported: PNG, JPG, JPEG, TIFF`)
      return
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max: ${MAX_MB} MB.`)
      return
    }
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const resp = await sonarAPI.upload(id!, fd)
      setUploaded(resp.data as typeof uploaded)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }, [id])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <PageHeader
        title="Upload Sonar Imagery"
        breadcrumbs={[{ label: 'Survey', to: `/surveys/${id}` }, { label: 'Upload' }]}
      />

      {/* Format notice */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <Info className="w-4 h-4 mt-0.5 shrink-0" />
        <div>
          <strong>Supported formats:</strong> PNG, JPG, JPEG, TIFF<br />
          Prototype currently supports image-based sonar input.
          Raw XTF/JSF ingestion is future scope.
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Drop or select sonar image</CardTitle></CardHeader>
        <CardBody>
          <div
            onDragOver={e => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={`
              border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
              ${dragging ? 'border-sonar-cyan bg-sonar-cyan/5' : 'border-slate-200 hover:border-ocean-400 hover:bg-slate-50'}
            `}
          >
            <Upload className={`w-10 h-10 mx-auto mb-3 ${dragging ? 'text-sonar-cyan' : 'text-slate-300'}`} />
            <p className="text-sm font-medium text-slate-600">
              {uploading ? 'Uploading…' : 'Drag & drop or click to select'}
            </p>
            <p className="text-xs text-slate-400 mt-1">PNG, JPG, JPEG, TIFF · max {MAX_MB} MB</p>
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              accept=".png,.jpg,.jpeg,.tiff,.tif"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
          </div>

          {error && (
            <div className="mt-4 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {uploaded && (
            <div className="mt-4 border border-emerald-200 bg-emerald-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <span className="font-semibold text-emerald-700 text-sm">Upload successful</span>
                {uploaded.data_source === 'DEMO' && (
                  <span className="text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">DEMO</span>
                )}
              </div>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                {[
                  ['Filename', uploaded.filename],
                  ['Size', `${(uploaded.file_size_bytes / 1024).toFixed(1)} KB`],
                  ['Dimensions', uploaded.width && uploaded.height ? `${uploaded.width}×${uploaded.height}` : 'Reading…'],
                  ['Data Source', uploaded.data_source],
                ].map(([k, v]) => (
                  <div key={k}><dt className="text-xs text-slate-400">{k}</dt><dd className="font-medium text-navy-900">{v}</dd></div>
                ))}
              </dl>
              <div className="mt-4 flex gap-3">
                <button
                  onClick={() => navigate(`/surveys/${id}/validation`)}
                  className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  Run Validation
                </button>
                <button
                  onClick={() => { setUploaded(null); setError('') }}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Upload Another
                </button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
