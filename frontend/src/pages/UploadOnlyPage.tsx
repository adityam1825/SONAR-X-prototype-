/**
 * SONAR-X — Upload-Only Entry Point
 *
 * The user's ONLY required action: select or drop a sonar image file.
 *
 * As soon as a valid file is received (drag-drop OR file-picker),
 * SONAR-X immediately:
 *   1. Fires the ingest API call (no button click required)
 *   2. Navigates to AutoProcessingPage
 *   3. AutoProcessingPage shows real pipeline progress until done
 *   4. On completion, navigates to Results
 *
 * There is NO "Analyse" button. There is NO manual form.
 */

import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileImage, AlertTriangle, Info, Radio } from 'lucide-react'
import { surveysAPI } from '../services/api'
import { ingestStore, type IngestResult } from '../services/ingestStore'

const ALLOWED_EXTS = ['.png', '.jpg', '.jpeg', '.tiff', '.tif']
const MAX_MB = 100

function humanBytes(n: number) {
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

function validateFile(f: File): string | null {
  const ext = '.' + (f.name.split('.').pop() ?? '').toLowerCase()
  if (!ALLOWED_EXTS.includes(ext))
    return `Unsupported type "${ext}". Use PNG, JPG, JPEG or TIFF.`
  if (f.size > MAX_MB * 1024 * 1024)
    return `File too large (${humanBytes(f.size)}). Max ${MAX_MB} MB.`
  return null
}

export default function UploadOnlyPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')

  /**
   * Core handler — fires immediately when files arrive.
   * No button click required.
   */
  const handleFiles = useCallback((incoming: FileList | File[]) => {
    setError('')
    const files = Array.from(incoming)
    if (!files.length) return

    // Validate every file first
    for (const f of files) {
      const err = validateFile(f)
      if (err) {
        setError(err)
        return
      }
    }

    // Build FormData
    const fd = new FormData()
    files.forEach(f => fd.append('files', f))

    // Fire the ingest API call and store the promise in the module store.
    // The promise resolves when the full pipeline completes on the backend.
    ingestStore.clear()
    ingestStore.promise = surveysAPI
      .ingest(fd, pct => { ingestStore.uploadProgress = pct })
      .then(resp => resp.data as IngestResult)

    // Navigate immediately — AutoProcessingPage awaits the promise
    navigate('/processing', { replace: false })
  }, [navigate])

  // Drag-and-drop
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }, [])
  const onDragLeave = useCallback(() => setDragging(false), [])
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  // File-picker change
  const onInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) handleFiles(e.target.files)
    // Reset input so the same file can be re-selected after an error
    e.target.value = ''
  }, [handleFiles])

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 sonar-grid-bg flex flex-col">
      {/* Header */}
      <header className="px-8 py-5 flex items-center gap-4">
        <div className="w-9 h-9 rounded-lg bg-sonar-cyan/20 border border-sonar-cyan/40 flex items-center justify-center">
          <Radio className="w-5 h-5 text-sonar-cyan" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white tracking-wider">SONAR-X</h1>
          <p className="text-xs text-slate-400">Marine Intelligence Platform</p>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-xl">

          {/* Title */}
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-white mb-3">New Sonar Survey</h2>
            <p className="text-slate-400 max-w-md mx-auto leading-relaxed text-sm">
              Drop your side-scan sonar image. SONAR-X automatically creates
              the survey, extracts metadata, runs the full analysis pipeline
              and generates a report.
            </p>
          </div>

          {/* Drop zone — single interaction target */}
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
            aria-label="Upload sonar image"
            className={`
              relative border-2 border-dashed rounded-2xl p-16 text-center
              cursor-pointer select-none
              transition-all duration-200 ease-out
              focus:outline-none focus:ring-2 focus:ring-sonar-cyan/50
              ${dragging
                ? 'border-sonar-cyan bg-sonar-cyan/8 scale-[1.01] shadow-lg shadow-sonar-cyan/10'
                : 'border-slate-600/60 bg-navy-800/40 hover:border-ocean-500/60 hover:bg-navy-800/60 hover:scale-[1.005]'
              }
            `}
          >
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              accept=".png,.jpg,.jpeg,.tiff,.tif"
              multiple
              onChange={onInputChange}
            />

            {/* Upload icon */}
            <div className={`
              w-20 h-20 mx-auto mb-6 rounded-2xl flex items-center justify-center
              transition-all duration-200
              ${dragging ? 'bg-sonar-cyan/20 scale-110' : 'bg-slate-700/40'}
            `}>
              <Upload className={`w-9 h-9 transition-colors ${dragging ? 'text-sonar-cyan' : 'text-slate-400'}`} />
            </div>

            <p className="text-white text-xl font-semibold mb-2">
              {dragging ? 'Release to analyse' : 'Drop sonar image here'}
            </p>
            <p className="text-slate-400 text-sm mb-6">or click to browse your files</p>

            {/* Format badge */}
            <div className="inline-flex items-center gap-2 bg-navy-700/60 border border-navy-600/60 rounded-full px-5 py-2">
              <FileImage className="w-4 h-4 text-slate-400 shrink-0" />
              <span className="text-xs text-slate-400 font-mono tracking-wide">
                JPG · PNG · TIFF
              </span>
              <span className="text-slate-600 text-xs">·</span>
              <span className="text-xs text-slate-500">max {MAX_MB} MB</span>
            </div>

            {/* "Instant analysis" label */}
            {!dragging && (
              <p className="text-xs text-sonar-cyan/60 mt-5 font-medium tracking-wide">
                Analysis starts automatically on upload
              </p>
            )}
          </div>

          {/* Validation error */}
          {error && (
            <div className="mt-5 flex items-start gap-3 bg-red-900/30 border border-red-600/40 rounded-xl px-4 py-3">
              <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm text-red-300">{error}</p>
                <button
                  onClick={() => setError('')}
                  className="text-xs text-red-400/70 hover:text-red-300 mt-1 underline"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Info note */}
          <div className="mt-6 flex items-start gap-2.5 bg-navy-800/30 border border-navy-700/40 rounded-xl px-4 py-3">
            <Info className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
            <p className="text-xs text-slate-500 leading-relaxed">
              GPS, timestamps and sonar geometry are extracted from the file where available.
              Missing metadata is never fabricated — processing continues with what is available.
            </p>
          </div>

          <p className="text-center text-xs text-slate-700 mt-5">
            Raw XTF/JSF ingestion is future scope · Image formats only in this prototype
          </p>
        </div>
      </main>
    </div>
  )
}
