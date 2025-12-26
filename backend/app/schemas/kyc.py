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

# Update forward references
KYCApplicationResponse.model_rebuild()

