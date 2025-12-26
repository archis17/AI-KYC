from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_admin_user
from app.models.user import User
from app.models.kyc import KYCApplication, AuditLog
from app.schemas.kyc import KYCApplicationResponse, AuditLogResponse

class RejectRequest(BaseModel):
    reason: Optional[str] = None

router = APIRouter()

async def verify_internal_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verify API key for internal/automated endpoints"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Please provide X-API-Key header."
        )
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True

@router.get("/applications", response_model=List[KYCApplicationResponse])
async def get_all_applications(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all KYC applications (admin only)"""
    query = db.query(KYCApplication)
    if status:
        query = query.filter(KYCApplication.status == status)
    applications = query.offset(skip).limit(limit).all()
    return applications

@router.get("/applications/{application_id}", response_model=KYCApplicationResponse)
async def get_application_admin(
    application_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get application details (admin only)"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.post("/applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Manually approve application (admin only)"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = "approved"
    
    # Create audit log
    audit_log = AuditLog(
        application_id=application_id,
        user_id=current_user.id,
        action="manual_approve",
        details={"approved_by": current_user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Application approved", "application_id": application_id}

@router.post("/applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Manually reject application (admin only)"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = "rejected"
    
    # Create audit log
    audit_log = AuditLog(
        application_id=application_id,
        user_id=current_user.id,
        action="manual_reject",
        details={"rejected_by": current_user.email, "reason": reason}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Application rejected", "application_id": application_id}

@router.get("/applications/{application_id}/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    application_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for an application (admin only)"""
    logs = db.query(AuditLog).filter(
        AuditLog.application_id == application_id
    ).order_by(AuditLog.created_at.desc()).all()
    return logs

# Internal endpoints for automated workflows (n8n, etc.)
@router.post("/internal/applications/{application_id}/approve")
async def approve_application_internal(
    application_id: int,
    api_key_verified: bool = Depends(verify_internal_api_key),
    db: Session = Depends(get_db)
):
    """Automated approve application (internal API key auth)"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = "approved"
    
    # Create audit log
    audit_log = AuditLog(
        application_id=application_id,
        user_id=None,  # System action
        action="auto_approve",
        details={"approved_by": "automated_workflow"}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Application approved", "application_id": application_id}

@router.post("/internal/applications/{application_id}/reject")
async def reject_application_internal(
    application_id: int,
    request: Optional[RejectRequest] = None,
    api_key_verified: bool = Depends(verify_internal_api_key),
    db: Session = Depends(get_db)
):
    """Automated reject application (internal API key auth)"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    reason = request.reason if request and request.reason else None
    application.status = "rejected"
    
    # Create audit log
    audit_log = AuditLog(
        application_id=application_id,
        user_id=None,  # System action
        action="auto_reject",
        details={"rejected_by": "automated_workflow", "reason": reason}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Application rejected", "application_id": application_id}

