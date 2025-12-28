export interface User {
  id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface Document {
  id: number
  application_id: number
  document_type: string
  file_name: string
  file_path: string
  file_size: number
  mime_type: string
  ocr_text: string | null
  ocr_confidence: number | null
  ocr_results: any
  extracted_entities: {
    name?: string
    dob?: string
    address?: string
    id_number?: string
  } | null
  validation_results: any
  created_at: string
}

export interface RiskScore {
  id: number
  application_id: number
  score: number
  decision: 'approved' | 'review' | 'rejected'
  reasoning: string
  risk_factors: any
  created_at: string
}

export interface KYCApplication {
  id: number
  user_id: number
  status: 'pending' | 'processing' | 'approved' | 'review' | 'rejected'
  created_at: string
  updated_at: string | null
  documents: Document[]
  risk_score: RiskScore | null
  processing_stage?: 'pending' | 'uploading' | 'ocr' | 'ner' | 'llm' | 'risk_scoring' | 'workflow' | 'completed' | 'unknown'
  processing_message?: string
}

export interface AuditLog {
  id: number
  application_id: number
  user_id: number | null
  action: string
  details: any
  created_at: string
}

export interface AnalyticsSummary {
  total_applications: number
  applications_today: number
  applications_this_month: number
  applications_this_year: number
  approved_count: number
  rejected_count: number
  review_count: number
  pending_count: number
  processing_count: number
  approval_rate: number
  rejection_rate: number
  average_risk_score: number | null
  average_processing_time_hours: number | null
}

export interface StatusDistribution {
  status: string
  count: number
  percentage: number
}

export interface RiskScoreDistribution {
  range: string
  count: number
  percentage: number
}

export interface TimeSeriesDataPoint {
  date: string
  count: number
  approved: number
  rejected: number
  review: number
}

export interface DocumentTypeStats {
  document_type: string
  count: number
  average_ocr_confidence: number | null
}

export interface RejectionReasonStats {
  reason: string
  count: number
  percentage: number
}

export interface AnalyticsResponse {
  summary: AnalyticsSummary
  status_distribution: StatusDistribution[]
  risk_score_distribution: RiskScoreDistribution[]
  applications_over_time: TimeSeriesDataPoint[]
  document_type_stats: DocumentTypeStats[]
  rejection_reasons: RejectionReasonStats[]
  period_start: string
  period_end: string
}

