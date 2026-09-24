// SONAR-X TypeScript Types

export interface User {
  id: string
  email: string
  full_name: string
  role: 'ADMIN' | 'OPERATOR' | 'ANALYST' | 'REVIEWER' | 'DEMO'
}

export interface AuthState {
  user: User | null
  access: string | null
  refresh: string | null
  isAuthenticated: boolean
}

export type DataSource = 'DEMO' | 'SURVEY'
export type SurveyStatus =
  | 'CREATED' | 'UPLOADING' | 'UPLOADED' | 'VALIDATING' | 'VALIDATED'
  | 'PREPROCESSING' | 'PREPROCESSED' | 'ANALYZING' | 'COMPLETED' | 'FAILED'
export type ChannelLayout = 'PORT' | 'STARBOARD' | 'BOTH'

export interface Survey {
  id: string
  survey_id: string
  name: string
  date: string
  area: string
  operator: string
  data_source: DataSource
  status: SurveyStatus
  is_demo: boolean
  detection_count: number
  latitude: number | null
  longitude: number | null
  altitude_m: number | null
  range_scale_mpp: number | null
  channel_layout: ChannelLayout
  already_gain_corrected: boolean
  already_slant_range_corrected: boolean
  already_processed: boolean
  notes: string
  created_at: string
}

export type Classification =
  | 'MARINE_DEBRIS'
  | 'NATURAL_FORMATION'
  | 'SONAR_ARTIFACT'
  | 'UNKNOWN_ANOMALY'

export type HazardLevel = 'NONE' | 'CAUTION' | 'HIGH_CAUTION'
export type FPRisk = 'LOW' | 'MEDIUM' | 'HIGH'
export type InferenceMode = 'DEMO' | 'CLASSICAL_CV' | 'YOLO'
export type VerificationStatus =
  | 'PENDING' | 'CONFIRMED' | 'REJECTED' | 'ESCALATED' | 'CLASS_CHANGED'

export interface SonarFingerprint {
  backscatter_score: number
  backscatter_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  texture_score: number
  texture_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  geometry_score: number
  geometry_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  shadow_score: number
  shadow_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  object_shadow_score: number
  object_shadow_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  seabed_context_score: number
  seabed_context_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  signal_quality_score: number
  signal_quality_status: 'STRONG' | 'MODERATE' | 'WEAK' | 'UNAVAILABLE'
  evidence_score: number
}

export interface Detection {
  id: string
  detection_uid: string
  survey_id: string
  survey_name: string
  classification: Classification
  confidence: number
  evidence_score: number
  false_positive_risk: FPRisk
  bbox_x: number | null
  bbox_y: number | null
  bbox_w: number | null
  bbox_h: number | null
  latitude: number | null
  longitude: number | null
  coordinate_note: string
  hazard_level: HazardLevel
  hazard_score: number
  hazard_indicators: string[]
  hazard_limited_data: boolean
  recommended_action: string
  supporting_evidence: string[]
  counter_evidence: string[]
  inference_mode: InferenceMode
  data_source: DataSource
  processing_summary: Record<string, string>
  verification_status: VerificationStatus
  debris_uid: string
  temporal_status: string | null
  fingerprint?: SonarFingerprint
  verifications?: Verification[]
  is_demo: boolean
  created_at: string
}

export interface Verification {
  id: string
  detection: string
  reviewer: string
  reviewer_email: string
  decision: string
  new_class: string
  comment: string
  timestamp: string
}

export interface ValidationCheck {
  name: string
  status: 'PASS' | 'FAIL' | 'WARN' | 'SKIP'
  value?: string
  note?: string
}

export interface ValidationResult {
  file_id: string
  filename: string
  result: 'VALID' | 'WARNING' | 'INVALID'
  checks: ValidationCheck[]
  warnings: string[]
  errors: string[]
}

export interface ProcessingStepInfo {
  status: 'APPLIED' | 'ESTIMATED' | 'SKIPPED' | 'NOT_APPLIED' | 'COMPLETE' | 'FAILED'
  reason?: string
  [key: string]: unknown
}

export interface PreprocessingResult {
  nadir: ProcessingStepInfo
  gain: ProcessingStepInfo
  slant_range: ProcessingStepInfo & { pixel_scale_gpp?: number }
  noise: ProcessingStepInfo
  contrast: ProcessingStepInfo
  quality: {
    status: string
    score: number
    level: 'GOOD' | 'MODERATE' | 'POOR' | 'UNKNOWN'
    saturation_ratio: number
    dropout_ratio: number
    snr_proxy: number
    image_contrast: number
    usable_area_ratio: number
    flags: string[]
  }
}

export interface TemporalMatch {
  id: string
  debris_object: string
  previous_observation: string
  candidate_observation: string | null
  distance_m: number | null
  fingerprint_similarity: number | null
  status: string
  notes: string
  verified_by: string | null
  verified_at: string | null
  verification_comment: string
  is_demo: boolean
}

export interface DebrisObject {
  debris_uid: string
  first_observed: string
  current_status: string
  classification: string
  hazard_level: HazardLevel
  is_demo: boolean
  observations: DetectionObservation[]
}

export interface DetectionObservation {
  id: string
  survey_id: string
  survey_name: string
  detection_id: string | null
  latitude: number | null
  longitude: number | null
  timestamp: string
  classification: string
  confidence: number
  hazard_level: HazardLevel
  fingerprint: Record<string, number>
}

export interface DashboardStats {
  total_surveys: number
  total_detections: number
  marine_debris: number
  natural_formation: number
  sonar_artifact: number
  unknown_anomaly: number
  hazard_flags: number
  pending_verification: number
}
