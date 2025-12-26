from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base

class DocumentType(str, enum.Enum):
    ID_CARD = "id_card"
    PASSPORT = "passport"
    PROOF_OF_ADDRESS = "proof_of_address"
    BANK_STATEMENT = "bank_statement"
    OTHER = "other"

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REVIEW = "review"
    REJECTED = "rejected"

class DecisionStatus(str, enum.Enum):
    APPROVED = "approved"
    REVIEW = "review"
    REJECTED = "rejected"

class KYCApplication(Base):
    __tablename__ = "kyc_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=ApplicationStatus.PENDING.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    risk_score = relationship("RiskScore", back_populates="application", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("kyc_applications.id"), nullable=False)
    document_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    
    # OCR Results
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_results = Column(JSON, nullable=True)  # Detailed OCR data with bounding boxes
    
    # Entity Extraction
    extracted_entities = Column(JSON, nullable=True)  # {name, dob, address, id_number}
    
    # Validation
    validation_results = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    application = relationship("KYCApplication", back_populates="documents")

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("kyc_applications.id"), unique=True, nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    decision = Column(String, nullable=False)  # approved, review, rejected
    reasoning = Column(Text, nullable=False)  # Human-readable explanation
    
    # Risk Factors Breakdown
    risk_factors = Column(JSON, nullable=True)  # Detailed breakdown
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    application = relationship("KYCApplication", back_populates="risk_score")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("kyc_applications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # upload, process, approve, reject, etc.
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    application = relationship("KYCApplication", back_populates="audit_logs")

