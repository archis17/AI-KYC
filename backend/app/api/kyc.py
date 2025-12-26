from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Tuple
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

def are_all_documents_ready(application: KYCApplication, db: Session) -> bool:
    """Check if all documents for an application have completed processing (OCR, NER, LLM)"""
    documents = db.query(Document).filter(
        Document.application_id == application.id
    ).all()
    
    if not documents:
        return False
    
    for doc in documents:
        # Check if OCR is complete
        # OCR is complete if:
        # 1. ocr_text is set (even if empty string, meaning OCR ran)
        # 2. OR ocr_results exists with processing_failed flag (OCR attempted but failed)
        ocr_complete = (
            (doc.ocr_text is not None) or  # OCR ran (even if empty result)
            (doc.ocr_results and doc.ocr_results.get("processing_failed"))  # OCR failed explicitly
        )
        
        # Check if NER is complete (extracted_entities is set, even if empty dict)
        ner_complete = doc.extracted_entities is not None
        
        # Check if LLM validation is complete (validation_results is set, even if error or skipped)
        llm_complete = doc.validation_results is not None
        
        if not (ocr_complete and ner_complete and llm_complete):
            print(f"Document {doc.id} not ready: ocr_complete={ocr_complete}, ner_complete={ner_complete}, llm_complete={llm_complete}")
            return False
    
    return True

def get_processing_stage(application: KYCApplication, db: Session) -> Tuple[str, str]:
    """Determine the current processing stage and message for an application"""
    if application.status == ApplicationStatus.PENDING.value:
        if not application.documents or len(application.documents) == 0:
            return "pending", "Waiting for documents to be uploaded"
        return "uploading", "Documents uploaded, processing starting..."
    
    if application.status in [ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value, ApplicationStatus.REVIEW.value]:
        return "completed", "Processing completed"
    
    if application.status == ApplicationStatus.PROCESSING.value:
        # Check which stage we're in based on document processing state
        if not application.documents or len(application.documents) == 0:
            return "pending", "Waiting for documents"
        
        # Check if all documents have OCR completed
        all_ocr_done = all(
            doc.ocr_text is not None or (doc.ocr_results and doc.ocr_results.get("processing_failed"))
            for doc in application.documents
        )
        if not all_ocr_done:
            return "ocr", "Extracting text from documents using OCR..."
        
        # Check if all documents have entity extraction
        all_ner_done = all(
            doc.extracted_entities is not None
            for doc in application.documents
        )
        if not all_ner_done:
            return "ner", "Analyzing entities and extracting information..."
        
        # Check if all documents have LLM validation
        all_llm_done = all(
            doc.validation_results is not None
            for doc in application.documents
        )
        if not all_llm_done:
            return "llm", "Validating documents with AI analysis..."
        
        # Check if risk score exists
        if not application.risk_score:
            return "risk_scoring", "Calculating risk score..."
        
        # Risk score exists but status is still processing, workflow might be running
        return "workflow", "Running automated workflow..."
    
    return "unknown", "Unknown status"

def enrich_application_response(application: KYCApplication, db: Session) -> dict:
    """Enrich application with processing stage information"""
    stage, message = get_processing_stage(application, db)
    # Convert SQLAlchemy model to dict and add processing info
    app_dict = {
        "id": application.id,
        "user_id": application.user_id,
        "status": application.status,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "documents": application.documents or [],
        "risk_score": application.risk_score,
        "processing_stage": stage,
        "processing_message": message
    }
    return app_dict

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
    # Enrich with processing stage
    return [KYCApplicationResponse(**enrich_application_response(app, db)) for app in applications]

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
    # Enrich with processing stage
    return KYCApplicationResponse(**enrich_application_response(application, db))

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
            
            # Log OCR results for debugging
            print(f"OCR Results for document {document_id}: confidence={document.ocr_confidence:.2f}, text_length={len(document.ocr_text)}, has_error={bool(ocr_results.get('detailed_results', {}).get('error'))}")
            
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
            elif document.ocr_confidence == 0.0 and not document.ocr_text:
                print(f"WARNING: OCR returned 0.0 confidence and no text for document {document_id}. This may indicate OCR failure or unreadable document.")
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
        
        print(f"Processing document {document_id} for application {application.id}. Total documents: {len(all_documents)}")
        
        # 4. LLM Validation (only if we have OCR text)
        if document.ocr_text and document.ocr_text.strip():
            try:
                # Only validate documents that have OCR text extracted
                ready_documents = [d for d in all_documents if d.ocr_text and d.ocr_text.strip()]
                
                if ready_documents:
                    print(f"Running LLM validation for document {document_id} with {len(ready_documents)} ready documents")
                    llm_service = LLMService()
                    validation_results = llm_service.validate_documents(ready_documents)
                    document.validation_results = validation_results
                    db.commit()
                    print(f"LLM validation completed for document {document_id}")
                else:
                    print(f"Skipping LLM validation for document {document_id}: No documents with OCR text ready")
                    document.validation_results = {"skipped": "No documents with OCR text ready"}
                    db.commit()
            except Exception as llm_error:
                print(f"Error in LLM validation for document {document_id}: {llm_error}")
                import traceback
                traceback.print_exc()
                document.validation_results = {"error": str(llm_error)}
                db.commit()
        else:
            print(f"Skipping LLM validation for document {document_id}: No OCR text available")
            document.validation_results = {"skipped": "No OCR text available"}
            db.commit()
        
        # 5. Check if all documents are ready before running risk scoring
        all_ready = are_all_documents_ready(application, db)
        print(f"All documents ready for application {application.id}: {all_ready}")
        
        if all_ready:
            # 6. Risk Scoring (only when all documents are processed)
            try:
                print(f"Running risk scoring for application {application.id} (all documents ready)")
                risk_service = RiskScoringService()
                risk_score = risk_service.calculate_risk_score(application, db)
                
                # 7. Trigger n8n workflow
                try:
                    n8n_service = N8NService()
                    n8n_service.trigger_workflow(application.id, risk_score)
                    print(f"n8n workflow triggered for application {application.id}")
                except Exception as n8n_error:
                    print(f"Error triggering n8n workflow for application {application.id}: {n8n_error}")
                
                # 8. Update application status based on decision (only when all documents are ready)
                if risk_score.decision == "approved":
                    application.status = ApplicationStatus.APPROVED.value
                elif risk_score.decision == "rejected":
                    application.status = ApplicationStatus.REJECTED.value
                else:
                    application.status = ApplicationStatus.REVIEW.value
                
                print(f"Application {application.id} status set to {application.status} (decision: {risk_score.decision})")
            except Exception as risk_error:
                print(f"Error in risk scoring for application {application.id}: {risk_error}")
                import traceback
                traceback.print_exc()
                application.status = ApplicationStatus.REVIEW.value
        else:
            # Keep status as PROCESSING until all documents are ready
            if application.status not in [ApplicationStatus.PROCESSING.value]:
                application.status = ApplicationStatus.PROCESSING.value
                print(f"Application {application.id} status kept as PROCESSING (waiting for all documents)")
        
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
