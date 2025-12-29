from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.kyc import ApplicationStatus, DecisionStatus

class DocumentUpload(BaseModel):
    document_type: str
    application_id: Optional[int] = None

class DocumentResponse(BaseModel):
    id: int
    application_id: int
    document_type: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_results: Optional[Dict[str, Any]] = None
    extracted_entities: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class KYCApplicationCreate(BaseModel):
    pass  # Created automatically on first document upload

class KYCApplicationResponse(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    documents: List[DocumentResponse] = []
    risk_score: Optional["RiskScoreResponse"] = None
    processing_stage: Optional[str] = None  # pending, ocr, ner, llm, risk_scoring, workflow, completed
    processing_message: Optional[str] = None  # Verbose status message
    
    class Config:
        from_attributes = True

class RiskScoreResponse(BaseModel):
    id: int
    application_id: int
    score: float
    decision: str
    reasoning: str
    risk_factors: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    application_id: int
    user_id: Optional[int]
    action: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analytics Schemas
class AnalyticsSummary(BaseModel):
    total_applications: int
    applications_today: int
    applications_this_month: int
    applications_this_year: int
    approved_count: int
    rejected_count: int
    review_count: int
    pending_count: int
    processing_count: int
    approval_rate: float  # percentage
    rejection_rate: float  # percentage
    average_risk_score: Optional[float] = None
    average_processing_time_hours: Optional[float] = None

class StatusDistribution(BaseModel):
    status: str
    count: int
    percentage: float

class RiskScoreDistribution(BaseModel):
    range: str  # e.g., "0-30", "31-60", "61-100"
    count: int
    percentage: float

class TimeSeriesDataPoint(BaseModel):
    date: str  # ISO date string
    count: int
    approved: int
    rejected: int
    review: int

class DocumentTypeStats(BaseModel):
    document_type: str
    count: int
    average_ocr_confidence: Optional[float] = None

class RejectionReasonStats(BaseModel):
    reason: str
    count: int
    percentage: float

class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    status_distribution: List[StatusDistribution]
    risk_score_distribution: List[RiskScoreDistribution]
    applications_over_time: List[TimeSeriesDataPoint]
    document_type_stats: List[DocumentTypeStats]
    rejection_reasons: List[RejectionReasonStats]
    period_start: str  # ISO date string
    period_end: str  # ISO date string

# Update forward references
KYCApplicationResponse.model_rebuild()

