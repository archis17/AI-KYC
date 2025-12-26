from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db, SessionLocal
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.kyc import KYCApplication, Document, ApplicationStatus
from app.schemas.kyc import (
    DocumentResponse, KYCApplicationResponse, DocumentUpload
)
from app.core.storage import get_storage
from app.services.ocr_service import OCRService
from app.services.ner_service import NERService
from app.services.llm_service import LLMService
from app.services.risk_scoring import RiskScoringService
from app.services.n8n_service import N8NService
import uuid
from pathlib import Path

router = APIRouter()

@router.post("/applications", response_model=KYCApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new KYC application"""
    application = KYCApplication(
        user_id=current_user.id,
        status=ApplicationStatus.PENDING.value
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

@router.get("/applications", response_model=List[KYCApplicationResponse])
async def get_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all KYC applications for current user"""
    applications = db.query(KYCApplication).filter(
        KYCApplication.user_id == current_user.id
    ).all()
    return applications

@router.get("/applications/{application_id}", response_model=KYCApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific KYC application"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id,
        KYCApplication.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.post("/applications/{application_id}/documents", response_model=DocumentResponse)
async def upload_document(
    application_id: int,
    document_type: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for KYC application"""
    # Verify application belongs to user
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id,
        KYCApplication.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed types: {allowed_types}"
        )
    
    # Read file data
    file_data = await file.read()
    file_size = len(file_data)
    
    # Generate unique file path
    file_ext = Path(file.filename).suffix
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"applications/{application_id}/{file_name}"
    
    # Save file using storage abstraction
    storage = get_storage()
    stored_path = storage.save(file_data, file_path)
    
    # Create document record
    document = Document(
        application_id=application_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=stored_path,
        file_size=file_size,
        mime_type=file.content_type
    )
    db.add(document)
    
    # Update application status
    application.status = ApplicationStatus.PROCESSING.value
    db.commit()
    db.refresh(document)
    
    # Process document in background
    background_tasks.add_task(process_document, document.id)
    
    return document

def process_document(document_id: int):
    """Process document through OCR, NER, LLM, and risk scoring"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        storage = get_storage()
        file_data = storage.get(document.file_path)
        
        # 1. OCR Processing
        try:
            ocr_service = OCRService()
            ocr_results = ocr_service.extract_text(file_data, document.mime_type)
            document.ocr_text = ocr_results.get("text", "")
            document.ocr_confidence = ocr_results.get("confidence", 0.0)
            document.ocr_results = ocr_results.get("detailed_results", {})
            
            # Check if OCR failed
            if ocr_results.get("detailed_results", {}).get("error"):
                error_info = ocr_results.get("detailed_results", {}).get("error", "Unknown OCR error")
                print(f"OCR processing failed for document {document_id}: {error_info}")
                # Continue processing with empty text, but mark the error
                document.ocr_results = {
                    **document.ocr_results,
                    "processing_failed": True,
                    "error_message": error_info
                }
        except Exception as ocr_error:
            print(f"Error initializing OCR service for document {document_id}: {ocr_error}")
            document.ocr_text = ""
            document.ocr_confidence = 0.0
            document.ocr_results = {
                "error": str(ocr_error),
                "error_type": "initialization_error",
                "processing_failed": True
            }
        
        # 2. Entity Extraction (only if OCR succeeded)
        if document.ocr_text:
            try:
                ner_service = NERService()
                entities = ner_service.extract_entities(document.ocr_text)
                document.extracted_entities = entities
            except Exception as ner_error:
                print(f"Error in entity extraction for document {document_id}: {ner_error}")
                document.extracted_entities = {}
        else:
            document.extracted_entities = {}
        
        db.commit()
        db.refresh(document)
        
        # 3. Get all documents for this application for cross-document validation
        application = db.query(KYCApplication).filter(
            KYCApplication.id == document.application_id
        ).first()
        all_documents = db.query(Document).filter(
            Document.application_id == application.id
        ).all()
        
        # 4. LLM Validation (only if we have OCR text)
        if document.ocr_text:
            try:
                llm_service = LLMService()
                validation_results = llm_service.validate_documents(all_documents)
                document.validation_results = validation_results
                db.commit()
            except Exception as llm_error:
                print(f"Error in LLM validation for document {document_id}: {llm_error}")
                document.validation_results = {"error": str(llm_error)}
                db.commit()
        
        # 5. Risk Scoring (after all documents are processed)
        try:
            risk_service = RiskScoringService()
            risk_score = risk_service.calculate_risk_score(application, db)
            
            # 6. Trigger n8n workflow
            try:
                n8n_service = N8NService()
                n8n_service.trigger_workflow(application.id, risk_score)
            except Exception as n8n_error:
                print(f"Error triggering n8n workflow for application {application.id}: {n8n_error}")
            
            # Update application status based on decision
            if risk_score.decision == "approved":
                application.status = ApplicationStatus.APPROVED.value
            elif risk_score.decision == "rejected":
                application.status = ApplicationStatus.REJECTED.value
            else:
                application.status = ApplicationStatus.REVIEW.value
        except Exception as risk_error:
            print(f"Error in risk scoring for application {application.id}: {risk_error}")
            application.status = ApplicationStatus.REVIEW.value
        
        db.commit()
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
        # Update application status to indicate error
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                application = db.query(KYCApplication).filter(
                    KYCApplication.id == document.application_id
                ).first()
                if application:
                    application.status = ApplicationStatus.REVIEW.value
                    db.commit()
        except:
            pass
    finally:
        db.close()

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document details"""
    document = db.query(Document).join(KYCApplication).filter(
        Document.id == document_id,
        KYCApplication.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
