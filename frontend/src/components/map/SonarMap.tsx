import { useEffect, useRef } from 'react'
import type { Detection } from '../../types'

declare global {
  interface Window { L: typeof import('leaflet') }
}

interface Props {
  detections: Detection[]
  center?: [number, number]
  zoom?: number
  showTemporalLine?: boolean
  previousLocation?: { lat: number; lng: number; label: string }
  candidateLocation?: { lat: number; lng: number; label: string }
}

export default function SonarMap({
  detections,
  center = [19.45, 72.84],
  zoom = 13,
  showTemporalLine,
  previousLocation,
  candidateLocation,
}: Props) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<unknown>(null)

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    // Dynamic import of Leaflet
    import('leaflet').then(L => {
      if (!mapRef.current || mapInstanceRef.current) return

      const map = L.map(mapRef.current, { center, zoom, zoomControl: true })
      mapInstanceRef.current = map

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map)

      // Detection markers
      detections.forEach(det => {
        if (det.latitude == null || det.longitude == null) return

        const isHighHazard = det.hazard_level === 'HIGH_CAUTION'
        const isCaution = det.hazard_level === 'CAUTION'
        const isVerified = det.verification_status === 'CONFIRMED'

        const color = isHighHazard ? '#DC2626'
          : isCaution ? '#D97706'
          : det.classification === 'MARINE_DEBRIS' ? '#2563EB'
          : det.classification === 'NATURAL_FORMATION' ? '#059669'
          : det.classification === 'SONAR_ARTIFACT' ? '#7C3AED'
          : '#EA580C'

        const icon = L.divIcon({
          html: `<div style="
            width:14px;height:14px;border-radius:50%;
            background:${color};border:2px solid white;
            box-shadow:0 1px 4px rgba(0,0,0,0.4);
            ${isVerified ? 'outline:2px solid #059669;outline-offset:2px;' : ''}
          "></div>`,
          className: '',
          iconSize: [14, 14],
          iconAnchor: [7, 7],
        })

        L.marker([det.latitude, det.longitude], { icon })
          .addTo(map)
          .bindPopup(`
            <div style="font-family:Inter,sans-serif;font-size:12px;min-width:180px">
              <p style="font-weight:700;color:#0A1628;margin:0 0 4px">${det.detection_uid}</p>
              <p style="margin:0 0 2px;color:#64748B">${det.classification.replace('_',' ')}</p>
              <p style="margin:0 0 2px">Confidence: <b>${det.confidence?.toFixed(0)}</b></p>
              <p style="margin:0 0 2px">Hazard: <b>${det.hazard_level}</b></p>
              <p style="margin:0 0 4px">Status: ${det.verification_status}</p>
              ${det.data_source === 'DEMO' ? '<span style="background:#FEF3C7;color:#92400E;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700">DEMO</span>' : ''}
            </div>
          `)
      })

      // Temporal relocation line
      if (showTemporalLine && previousLocation && candidateLocation) {
        const prev = L.latLng(previousLocation.lat, previousLocation.lng)
        const cand = L.latLng(candidateLocation.lat, candidateLocation.lng)

        L.polyline([prev, cand], {
          color: '#7C3AED',
          weight: 2,
          dashArray: '8 6',
          opacity: 0.8,
        }).addTo(map).bindPopup('POTENTIAL RELOCATION PATH — requires human verification')

        L.marker(prev, {
          icon: L.divIcon({
            html: `<div style="background:#6B7280;border-radius:50%;width:12px;height:12px;border:2px solid white"></div>`,
            className: '', iconSize: [12, 12], iconAnchor: [6, 6],
          })
        }).addTo(map).bindPopup(`PREVIOUS LOCATION: ${previousLocation.label}`)

        L.marker(cand, {
          icon: L.divIcon({
            html: `<div style="background:#7C3AED;border-radius:50%;width:12px;height:12px;border:2px solid white"></div>`,
            className: '', iconSize: [12, 12], iconAnchor: [6, 6],
          })
        }).addTo(map).bindPopup(`CANDIDATE LOCATION: ${candidateLocation.label}`)
      }
    })

    return () => {
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  return <div ref={mapRef} className="w-full h-full rounded-lg" style={{ minHeight: 400 }} />
}
