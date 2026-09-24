/**
 * SONAR-X Ingest Store
 *
 * Module-level singleton that holds the in-flight ingest promise so it
 * can be shared between UploadOnlyPage (which starts the call) and
 * AutoProcessingPage (which consumes the result).
 *
 * Using a module-level object is intentional: FormData and Promises
 * cannot survive serialization through React Router navigation state.
 * This is not a global state library — it is a single-use hand-off
 * between two consecutive pages in the same browser session.
 */

export interface IngestResult {
  survey_pk: number
  survey_id: string
  survey_name: string
  survey_date: string
  status: string
  inference_mode: string
  detection_count: number
  metadata_summary: { found: string[]; unavailable: string[] }
  report: { status: string; report_id?: string; download_url?: string }
}

interface IngestStore {
  promise: Promise<IngestResult> | null
  uploadProgress: number
  clear: () => void
}

export const ingestStore: IngestStore = {
  promise: null,
  uploadProgress: 0,
  clear() {
    this.promise = null
    this.uploadProgress = 0
  },
}
