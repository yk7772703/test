from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.crm import Customer, CustomerType, Contact, Opportunity, OpportunityStage, Activity, Contract
from app.models.compliance import KYCRecord
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.sanctions_service import screen_name, create_sanctions_alert
import uuid

router = APIRouter(prefix="/crm", tags=["crm"])


class CustomerIn(BaseModel):
    customer_type: str = "company"
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    jurisdiction: str = "US"
    tax_id: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms: int = 30
    currency: str = "USD"


@router.get("/customers")
def list_customers(
    search: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    kyc_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Customer).filter(Customer.is_active == True)
    if search:
        q = q.filter(Customer.name.ilike(f"%{search}%"))
    if customer_type:
        q = q.filter(Customer.customer_type == customer_type)
    if jurisdiction:
        q = q.filter(Customer.jurisdiction == jurisdiction)
    if kyc_status:
        q = q.filter(Customer.kyc_status == kyc_status)
    total = q.count()
    items = q.order_by(Customer.name).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(c.id),
                "customer_number": c.customer_number,
                "name": c.name,
                "customer_type": c.customer_type.value,
                "email": c.email,
                "country": c.country,
                "jurisdiction": c.jurisdiction,
                "kyc_status": c.kyc_status,
                "risk_level": c.risk_level,
                "is_sanctioned": c.is_sanctioned,
                "credit_limit": float(c.credit_limit) if c.credit_limit else None,
            }
            for c in items
        ],
    }


@router.post("/customers")
def create_customer(
    req: CustomerIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(Customer).count()
    cust_num = f"CUST-{count + 1:05d}"

    customer = Customer(
        customer_number=cust_num,
        customer_type=CustomerType(req.customer_type),
        name=req.name,
        email=req.email,
        phone=req.phone,
        website=req.website,
        industry=req.industry,
        country=req.country,
        jurisdiction=req.jurisdiction,
        tax_id=req.tax_id,
        credit_limit=req.credit_limit,
        payment_terms=req.payment_terms,
        currency=req.currency,
        assigned_to=current_user.id,
    )
    db.add(customer)
    db.flush()

    # Create initial KYC record
    kyc = KYCRecord(customer_id=customer.id, status="pending")
    db.add(kyc)
    db.commit()
    db.refresh(customer)

    # Auto-screen against sanctions in background
    async def _screen():
        matches = screen_name(req.name, db)
        if matches:
            customer.is_sanctioned = True
            customer.kyc_status = "flagged"
            create_sanctions_alert("customer", customer.id, req.name, matches, db)
            db.commit()

    background_tasks.add_task(_screen)

    return {"id": str(customer.id), "customer_number": cust_num}


@router.get("/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "id": str(c.id),
        "customer_number": c.customer_number,
        "name": c.name,
        "customer_type": c.customer_type.value,
        "email": c.email,
        "phone": c.phone,
        "website": c.website,
        "industry": c.industry,
        "country": c.country,
        "jurisdiction": c.jurisdiction,
        "tax_id": c.tax_id,
        "credit_limit": float(c.credit_limit) if c.credit_limit else None,
        "payment_terms": c.payment_terms,
        "currency": c.currency,
        "kyc_status": c.kyc_status,
        "risk_level": c.risk_level,
        "is_sanctioned": c.is_sanctioned,
    }


@router.post("/customers/{customer_id}/screen-sanctions")
def screen_customer_sanctions(
    customer_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    matches = screen_name(customer.name, db)
    if matches:
        customer.is_sanctioned = True
        alert = create_sanctions_alert("customer", customer.id, customer.name, matches, db)

    from datetime import datetime, timezone
    kyc = db.query(KYCRecord).filter(KYCRecord.customer_id == customer_id).first()
    if kyc:
        kyc.sanctions_checked = True
        kyc.sanctions_checked_at = datetime.now(timezone.utc)
        db.commit()

    return {"matches": matches, "is_sanctioned": bool(matches)}


# ─── Opportunities ────────────────────────────────────────────────────────────

@router.get("/opportunities")
def list_opportunities(
    stage: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Opportunity)
    if stage:
        q = q.filter(Opportunity.stage == stage)
    if customer_id:
        q = q.filter(Opportunity.customer_id == customer_id)
    total = q.count()
    items = q.order_by(desc(Opportunity.created_at)).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(o.id),
                "name": o.name,
                "customer_id": str(o.customer_id),
                "stage": o.stage.value,
                "value": float(o.value) if o.value else None,
                "currency": o.currency,
                "probability": float(o.probability) if o.probability else None,
                "expected_close_date": o.expected_close_date.isoformat() if o.expected_close_date else None,
            }
            for o in items
        ],
    }


@router.get("/dashboard")
def crm_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_customers = db.query(func.count(Customer.id)).filter(Customer.is_active == True).scalar()
    flagged = db.query(func.count(Customer.id)).filter(Customer.is_sanctioned == True).scalar()
    kyc_pending = db.query(func.count(Customer.id)).filter(Customer.kyc_status == "pending").scalar()

    pipeline_value = db.query(func.sum(Opportunity.value)).filter(
        Opportunity.stage.in_([OpportunityStage.QUALIFIED, OpportunityStage.PROPOSAL, OpportunityStage.NEGOTIATION])
    ).scalar() or 0

    by_stage = db.query(
        Opportunity.stage, func.count(Opportunity.id), func.sum(Opportunity.value)
    ).group_by(Opportunity.stage).all()

    return {
        "total_customers": total_customers,
        "sanctioned_customers": flagged,
        "kyc_pending": kyc_pending,
        "pipeline_value": float(pipeline_value),
        "by_stage": [
            {"stage": s.value, "count": c, "value": float(v or 0)}
            for s, c, v in by_stage
        ],
    }
