import { useState } from 'react'
import { Save, Info } from 'lucide-react'
import { Card, CardBody, CardHeader, CardTitle } from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    detection_threshold: 0.35,
    temporal_search_radius: 500,
    fingerprint_similarity_threshold: 0.65,
    demo_mode: true,
    inference_mode: 'DEMO',
    median_filter_size: 3,
    clahe_clip_limit: 2.0,
    clahe_tile_size: 8,
    // Fusion weights (configurable demo values)
    w_backscatter: 0.15,
    w_texture: 0.15,
    w_geometry: 0.15,
    w_shadow: 0.20,
    w_object_shadow: 0.15,
    w_seabed_context: 0.10,
    w_signal_quality: 0.10,
    // Hazard thresholds
    large_extent_threshold: 5000,
    hazard_caution_score: 30,
    hazard_high_caution_score: 60,
  })

  const [saved, setSaved] = useState(false)

  const set = (k: string, v: string | number | boolean) => setSettings(s => ({ ...s, [k]: v }))

  const saveSettings = () => {
    // In a full implementation this would call a settings API
    localStorage.setItem('sonarx_settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  const inputClass = 'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ocean-500 transition-all'
  const labelClass = 'block text-xs font-semibold text-slate-600 mb-1'

  const totalWeight = settings.w_backscatter + settings.w_texture + settings.w_geometry +
    settings.w_shadow + settings.w_object_shadow + settings.w_seabed_context + settings.w_signal_quality

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        title="System Settings"
        subtitle="Configure detection, fusion, hazard, and temporal parameters"
        breadcrumbs={[{ label: 'Settings' }]}
        actions={
          <button
            onClick={saveSettings}
            className="flex items-center gap-2 bg-ocean-600 hover:bg-ocean-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Save className="w-4 h-4" />
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
        }
      />

      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-start gap-2 text-sm text-amber-700">
        <Info className="w-4 h-4 mt-0.5 shrink-0" />
        <span>
          Configurable values are <strong>demonstration parameters</strong>, not scientifically validated coefficients.
          Evidence fusion weights are normalised at runtime.
        </span>
      </div>

      <Card>
        <CardHeader><CardTitle>Inference Mode</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Inference Mode</label>
            <select className={inputClass} value={settings.inference_mode} onChange={e => set('inference_mode', e.target.value)}>
              <option value="DEMO">DEMO</option>
              <option value="CLASSICAL_CV">CLASSICAL CV (fallback)</option>
              <option value="YOLO">YOLO (requires model file)</option>
            </select>
            <p className="text-xs text-slate-400 mt-1">
              YOLO requires AI_MODEL_PATH to be set. Classical CV is NOT a trained AI model.
            </p>
          </div>
          <div className="flex items-center gap-2 pt-5">
            <input type="checkbox" id="demo_mode" checked={settings.demo_mode}
              onChange={e => set('demo_mode', e.target.checked)} className="w-4 h-4 rounded" />
            <label htmlFor="demo_mode" className="text-sm text-slate-700">Demo Mode (use cached results)</label>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Detection Parameters</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Detection Confidence Threshold</label>
            <input type="number" step="0.01" min="0" max="1" className={inputClass}
              value={settings.detection_threshold} onChange={e => set('detection_threshold', parseFloat(e.target.value))} />
          </div>
          <div>
            <label className={labelClass}>Large Extent Threshold (px²)</label>
            <input type="number" className={inputClass}
              value={settings.large_extent_threshold} onChange={e => set('large_extent_threshold', parseInt(e.target.value))} />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Preprocessing Parameters</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>Median Filter Size</label>
            <input type="number" min="1" step="2" className={inputClass}
              value={settings.median_filter_size} onChange={e => set('median_filter_size', parseInt(e.target.value))} />
          </div>
          <div>
            <label className={labelClass}>CLAHE Clip Limit</label>
            <input type="number" step="0.1" min="0.5" max="10" className={inputClass}
              value={settings.clahe_clip_limit} onChange={e => set('clahe_clip_limit', parseFloat(e.target.value))} />
          </div>
          <div>
            <label className={labelClass}>CLAHE Tile Size</label>
            <input type="number" step="1" min="4" className={inputClass}
              value={settings.clahe_tile_size} onChange={e => set('clahe_tile_size', parseInt(e.target.value))} />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evidence Fusion Weights</CardTitle>
          <p className="text-xs text-amber-600 mt-0.5">
            Configurable demonstration values — NOT scientifically validated coefficients.
            Weights are normalised at runtime (current sum: {totalWeight.toFixed(2)}).
          </p>
        </CardHeader>
        <CardBody className="grid grid-cols-2 gap-3">
          {[
            { key: 'w_backscatter', label: 'Backscatter' },
            { key: 'w_texture', label: 'Texture' },
            { key: 'w_geometry', label: 'Geometry' },
            { key: 'w_shadow', label: 'Acoustic Shadow' },
            { key: 'w_object_shadow', label: 'Object-Shadow' },
            { key: 'w_seabed_context', label: 'Seabed Context' },
            { key: 'w_signal_quality', label: 'Signal Quality' },
          ].map(({ key, label }) => (
            <div key={key}>
              <label className={labelClass}>{label}</label>
              <input type="number" step="0.01" min="0" max="1" className={inputClass}
                value={((settings as unknown) as Record<string, number>)[key]}
                onChange={e => set(key, parseFloat(e.target.value))} />
            </div>
          ))}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Temporal Parameters</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Search Radius (m)</label>
            <input type="number" className={inputClass}
              value={settings.temporal_search_radius} onChange={e => set('temporal_search_radius', parseInt(e.target.value))} />
            <p className="text-xs text-slate-400 mt-1">Haversine radius for candidate matching</p>
          </div>
          <div>
            <label className={labelClass}>Fingerprint Similarity Threshold</label>
            <input type="number" step="0.01" min="0" max="1" className={inputClass}
              value={settings.fingerprint_similarity_threshold} onChange={e => set('fingerprint_similarity_threshold', parseFloat(e.target.value))} />
            <p className="text-xs text-slate-400 mt-1">Minimum score for POTENTIALLY_RELOCATED</p>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
