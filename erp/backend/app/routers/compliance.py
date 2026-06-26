from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from app.database import get_db
from app.models.compliance import (
    ComplianceAlert, AlertStatus, AlertSeverity,
    RegulatoryUpdate, SanctionList, SanctionedEntity, KYCRecord, AuditLog
)
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.sanctions_service import run_daily_update, screen_name
from app.services.regulatory_service import fetch_regulatory_updates
import uuid

router = APIRouter(prefix="/compliance", tags=["compliance"])


# ─── Sanctions ────────────────────────────────────────────────────────────────

@router.get("/sanctions/lists")
def get_sanction_lists(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    lists = db.query(SanctionList).order_by(desc(SanctionList.last_updated)).all()
    return [
        {
            "id": str(sl.id),
            "source": sl.source.value,
            "last_updated": sl.last_updated.isoformat() if sl.last_updated else None,
            "entry_count": sl.entry_count,
            "is_current": sl.is_current,
        }
        for sl in lists
    ]


@router.post("/sanctions/update")
async def trigger_sanctions_update(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    async def _run():
        await run_daily_update(db)
    background_tasks.add_task(_run)
    return {"message": "Sanctions update triggered in background"}


@router.post("/sanctions/screen")
def screen_entity(
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    name = payload.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    threshold = float(payload.get("threshold", 0.85))
    matches = screen_name(name, db, threshold=threshold)
    return {"name": name, "threshold": threshold, "matches": matches}


# ─── Alerts ───────────────────────────────────────────────────────────────────

@router.get("/alerts")
def get_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(ComplianceAlert)
    if status:
        q = q.filter(ComplianceAlert.status == status)
    if severity:
        q = q.filter(ComplianceAlert.severity == severity)
    total = q.count()
    alerts = q.order_by(desc(ComplianceAlert.created_at)).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "severity": a.severity.value,
                "status": a.status.value,
                "title": a.title,
                "description": a.description,
                "match_score": a.match_score,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    }


@router.patch("/alerts/{alert_id}")
def update_alert(
    alert_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(ComplianceAlert).filter(ComplianceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if "status" in payload:
        alert.status = AlertStatus(payload["status"])
    if "resolution_notes" in payload:
        alert.resolution_notes = payload["resolution_notes"]
        alert.resolved_by = current_user.id
        from datetime import datetime, timezone
        alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    return {"message": "Alert updated"}


@router.get("/alerts/stats")
def get_alert_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    by_severity = db.query(
        ComplianceAlert.severity, func.count(ComplianceAlert.id)
    ).filter(ComplianceAlert.status == AlertStatus.OPEN).group_by(ComplianceAlert.severity).all()

    by_status = db.query(
        ComplianceAlert.status, func.count(ComplianceAlert.id)
    ).group_by(ComplianceAlert.status).all()

    return {
        "open_by_severity": {s.value: c for s, c in by_severity},
        "by_status": {s.value: c for s, c in by_status},
        "total_open": db.query(ComplianceAlert).filter(ComplianceAlert.status == AlertStatus.OPEN).count(),
    }


# ─── Regulatory Updates ───────────────────────────────────────────────────────

@router.get("/regulatory-updates")
def get_regulatory_updates(
    jurisdiction: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(RegulatoryUpdate)
    if jurisdiction:
        q = q.filter(RegulatoryUpdate.jurisdiction == jurisdiction)
    if category:
        q = q.filter(RegulatoryUpdate.category == category)
    if unread_only:
        q = q.filter(RegulatoryUpdate.is_read == False)
    total = q.count()
    items = q.order_by(desc(RegulatoryUpdate.created_at)).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(u.id),
                "jurisdiction": u.jurisdiction,
                "category": u.category,
                "title": u.title,
                "summary": u.summary,
                "source_url": u.source_url,
                "severity": u.severity.value,
                "requires_action": u.requires_action,
                "is_read": u.is_read,
                "created_at": u.created_at.isoformat(),
            }
            for u in items
        ],
    }


@router.post("/regulatory-updates/refresh")
async def refresh_regulatory_updates(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    async def _run():
        await fetch_regulatory_updates(db)
    background_tasks.add_task(_run)
    return {"message": "Regulatory update refresh triggered"}


@router.patch("/regulatory-updates/{update_id}/read")
def mark_as_read(update_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    update = db.query(RegulatoryUpdate).filter(RegulatoryUpdate.id == update_id).first()
    if not update:
        raise HTTPException(status_code=404, detail="Not found")
    update.is_read = True
    db.commit()
    return {"message": "Marked as read"}


# ─── KYC ──────────────────────────────────────────────────────────────────────

@router.get("/kyc")
def get_kyc_records(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(KYCRecord)
    if status:
        q = q.filter(KYCRecord.status == status)
    total = q.count()
    items = q.order_by(desc(KYCRecord.created_at)).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(k.id),
                "customer_id": str(k.customer_id),
                "status": k.status,
                "risk_level": k.risk_level.value if k.risk_level else None,
                "sanctions_checked": k.sanctions_checked,
                "sanctions_checked_at": k.sanctions_checked_at.isoformat() if k.sanctions_checked_at else None,
                "pep_checked": k.pep_checked,
                "aml_score": k.aml_score,
                "created_at": k.created_at.isoformat(),
            }
            for k in items
        ],
    }


# ─── Audit Log ────────────────────────────────────────────────────────────────

@router.get("/audit-log")
def get_audit_log(
    module: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(AuditLog)
    if module:
        q = q.filter(AuditLog.module == module)
    total = q.count()
    items = q.order_by(desc(AuditLog.created_at)).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(l.id),
                "user_id": str(l.user_id) if l.user_id else None,
                "action": l.action,
                "module": l.module,
                "entity_type": l.entity_type,
                "entity_id": str(l.entity_id) if l.entity_id else None,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in items
        ],
    }
