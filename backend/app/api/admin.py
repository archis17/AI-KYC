from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_admin_user
from app.models.user import User
from app.models.kyc import KYCApplication, AuditLog, RiskScore, Document
from app.schemas.kyc import (
    KYCApplicationResponse, 
    AuditLogResponse,
    AnalyticsResponse,
    AnalyticsSummary,
    StatusDistribution,
    RiskScoreDistribution,
    TimeSeriesDataPoint,
    DocumentTypeStats,
    RejectionReasonStats
)
from app.api.kyc import enrich_application_response

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
    # Enrich with processing stage
    return [KYCApplicationResponse(**enrich_application_response(app, db)) for app in applications]

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
    # Enrich with processing stage
    return KYCApplicationResponse(**enrich_application_response(application, db))

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

@router.delete("/applications/{application_id}")
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete application and all related data (admin only)"""
    application = db.query(KYCApplication).filter(
        KYCApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Create audit log before deletion
    audit_log = AuditLog(
        application_id=application_id,
        user_id=current_user.id,
        action="delete",
        details={"deleted_by": current_user.email}
    )
    db.add(audit_log)
    
    # Delete application (cascading deletes will handle documents, risk_scores, audit_logs)
    db.delete(application)
    db.commit()
    
    return {"message": "Application deleted successfully", "application_id": application_id}

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics data (admin only)"""
    # Parse dates or use defaults
    if start_date:
        try:
            # Handle date-only strings (YYYY-MM-DD)
            if len(start_date) == 10:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            start_dt = datetime.now() - timedelta(days=90)
    else:
        start_dt = datetime.now() - timedelta(days=90)  # Last 90 days
    
    if end_date:
        try:
            # Handle date-only strings (YYYY-MM-DD) - set to end of day
            if len(end_date) == 10:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            else:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            end_dt = datetime.now()
    else:
        end_dt = datetime.now()
    
    # Base query with date filter
    base_query = db.query(KYCApplication).filter(
        KYCApplication.created_at >= start_dt,
        KYCApplication.created_at <= end_dt
    )
    
    # Summary Statistics
    total_applications = base_query.count()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    applications_today = db.query(KYCApplication).filter(
        KYCApplication.created_at >= today
    ).count()
    
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    applications_this_month = db.query(KYCApplication).filter(
        KYCApplication.created_at >= month_start
    ).count()
    
    year_start = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    applications_this_year = db.query(KYCApplication).filter(
        KYCApplication.created_at >= year_start
    ).count()
    
    # Status counts
    status_counts = db.query(
        KYCApplication.status,
        func.count(KYCApplication.id).label('count')
    ).filter(
        KYCApplication.created_at >= start_dt,
        KYCApplication.created_at <= end_dt
    ).group_by(KYCApplication.status).all()
    
    status_dict = {status: count for status, count in status_counts}
    approved_count = status_dict.get('approved', 0)
    rejected_count = status_dict.get('rejected', 0)
    review_count = status_dict.get('review', 0)
    pending_count = status_dict.get('pending', 0)
    processing_count = status_dict.get('processing', 0)
    
    # Calculate rates
    completed_count = approved_count + rejected_count
    approval_rate = (approved_count / completed_count * 100) if completed_count > 0 else 0.0
    rejection_rate = (rejected_count / completed_count * 100) if completed_count > 0 else 0.0
    
    # Average risk score
    avg_risk_result = db.query(func.avg(RiskScore.score)).join(
        KYCApplication, RiskScore.application_id == KYCApplication.id
    ).filter(
        KYCApplication.created_at >= start_dt,
        KYCApplication.created_at <= end_dt
    ).scalar()
    average_risk_score = float(avg_risk_result) if avg_risk_result else None
    
    # Average processing time (for completed applications)
    completed_apps = base_query.filter(
        KYCApplication.status.in_(['approved', 'rejected'])
    ).all()
    
    processing_times = []
    for app in completed_apps:
        if app.updated_at and app.created_at:
            delta = app.updated_at - app.created_at
            hours = delta.total_seconds() / 3600
            processing_times.append(hours)
    
    average_processing_time_hours = (
        sum(processing_times) / len(processing_times) 
        if processing_times else None
    )
    
    summary = AnalyticsSummary(
        total_applications=total_applications,
        applications_today=applications_today,
        applications_this_month=applications_this_month,
        applications_this_year=applications_this_year,
        approved_count=approved_count,
        rejected_count=rejected_count,
        review_count=review_count,
        pending_count=pending_count,
        processing_count=processing_count,
        approval_rate=round(approval_rate, 2),
        rejection_rate=round(rejection_rate, 2),
        average_risk_score=round(average_risk_score, 2) if average_risk_score else None,
        average_processing_time_hours=round(average_processing_time_hours, 2) if average_processing_time_hours else None
    )
    
    # Status Distribution
    status_distribution = []
    for status, count in status_counts:
        percentage = (count / total_applications * 100) if total_applications > 0 else 0.0
        status_distribution.append(StatusDistribution(
            status=status,
            count=count,
            percentage=round(percentage, 2)
        ))
    
    # Risk Score Distribution
    risk_ranges = [
        (0, 30, "0-30"),
        (31, 60, "31-60"),
        (61, 100, "61-100")
    ]
    
    risk_score_distribution = []
    total_with_risk = db.query(func.count(RiskScore.id)).join(
        KYCApplication, RiskScore.application_id == KYCApplication.id
    ).filter(
        KYCApplication.created_at >= start_dt,
        KYCApplication.created_at <= end_dt
    ).scalar() or 0
    
    for min_score, max_score, range_label in risk_ranges:
        count = db.query(func.count(RiskScore.id)).join(
            KYCApplication, RiskScore.application_id == KYCApplication.id
        ).filter(
            and_(
                KYCApplication.created_at >= start_dt,
                KYCApplication.created_at <= end_dt,
                RiskScore.score >= min_score,
                RiskScore.score <= max_score
            )
        ).scalar() or 0
        
        percentage = (count / total_with_risk * 100) if total_with_risk > 0 else 0.0
        risk_score_distribution.append(RiskScoreDistribution(
            range=range_label,
            count=count,
            percentage=round(percentage, 2)
        ))
    
    # Applications Over Time (daily aggregation)
    time_series_query = db.query(
        func.date(KYCApplication.created_at).label('date'),
        func.count(KYCApplication.id).label('count'),
        func.sum(case((KYCApplication.status == 'approved', 1), else_=0)).label('approved'),
        func.sum(case((KYCApplication.status == 'rejected', 1), else_=0)).label('rejected'),
        func.sum(case((KYCApplication.status == 'review', 1), else_=0)).label('review')
    ).filter(
        KYCApplication.created_at >= start_dt,
        KYCApplication.created_at <= end_dt
    ).group_by(func.date(KYCApplication.created_at)).order_by('date').all()
    
    applications_over_time = [
        TimeSeriesDataPoint(
            date=row.date.isoformat(),
            count=row.count,
            approved=int(row.approved or 0),
            rejected=int(row.rejected or 0),
            review=int(row.review or 0)
        )
        for row in time_series_query
    ]
    
    # Document Type Statistics
    doc_stats_query = db.query(
        Document.document_type,
        func.count(Document.id).label('count'),
        func.avg(Document.ocr_confidence).label('avg_confidence')
    ).join(
        KYCApplication, Document.application_id == KYCApplication.id
    ).filter(
        KYCApplication.created_at >= start_dt,
        KYCApplication.created_at <= end_dt
    ).group_by(Document.document_type).all()
    
    document_type_stats = [
        DocumentTypeStats(
            document_type=row.document_type,
            count=row.count,
            average_ocr_confidence=round(float(row.avg_confidence), 2) if row.avg_confidence else None
        )
        for row in doc_stats_query
    ]
    
    # Rejection Reasons (from audit logs)
    rejection_logs = db.query(AuditLog).join(
        KYCApplication, AuditLog.application_id == KYCApplication.id
    ).filter(
        and_(
            AuditLog.action.in_(['manual_reject', 'auto_reject']),
            KYCApplication.created_at >= start_dt,
            KYCApplication.created_at <= end_dt
        )
    ).all()
    
    # Extract reasons from audit log details
    reason_counts = {}
    for log in rejection_logs:
        reason = "No reason provided"
        if log.details and isinstance(log.details, dict):
            reason = log.details.get('reason', 'No reason provided')
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    total_rejections = sum(reason_counts.values())
    rejection_reasons = [
        RejectionReasonStats(
            reason=reason,
            count=count,
            percentage=round((count / total_rejections * 100), 2) if total_rejections > 0 else 0.0
        )
        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return AnalyticsResponse(
        summary=summary,
        status_distribution=status_distribution,
        risk_score_distribution=risk_score_distribution,
        applications_over_time=applications_over_time,
        document_type_stats=document_type_stats,
        rejection_reasons=rejection_reasons,
        period_start=start_dt.isoformat(),
        period_end=end_dt.isoformat()
    )

