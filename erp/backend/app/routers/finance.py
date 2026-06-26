from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from typing import Optional
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from app.database import get_db
from app.models.finance import (
    Account, AccountType, Invoice, InvoiceStatus, InvoiceItem,
    Payment, JournalEntry, JournalLine, Budget, TaxRate
)
from app.routers.auth import get_current_user
from app.models.user import User
import uuid

router = APIRouter(prefix="/finance", tags=["finance"])


# ─── Accounts ────────────────────────────────────────────────────────────────

@router.get("/accounts")
def list_accounts(
    account_type: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Account).filter(Account.is_active == True)
    if account_type:
        q = q.filter(Account.account_type == account_type)
    if jurisdiction:
        q = q.filter(Account.jurisdiction == jurisdiction)
    accounts = q.order_by(Account.code).all()
    return [
        {
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "account_type": a.account_type.value,
            "currency": a.currency,
            "balance": float(a.balance),
            "jurisdiction": a.jurisdiction,
        }
        for a in accounts
    ]


@router.post("/accounts")
def create_account(payload: dict, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    account = Account(
        code=payload["code"],
        name=payload["name"],
        account_type=AccountType(payload["account_type"]),
        currency=payload.get("currency", "USD"),
        jurisdiction=payload.get("jurisdiction", "US"),
        description=payload.get("description"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"id": str(account.id), "code": account.code, "name": account.name}


# ─── Invoices ─────────────────────────────────────────────────────────────────

class InvoiceItemIn(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    tax_rate_id: Optional[str] = None


class InvoiceIn(BaseModel):
    invoice_type: str = "AR"
    customer_id: Optional[str] = None
    date: date
    due_date: date
    currency: str = "USD"
    jurisdiction: str = "US"
    notes: Optional[str] = None
    items: list[InvoiceItemIn]


@router.get("/invoices")
def list_invoices(
    invoice_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Invoice)
    if invoice_type:
        q = q.filter(Invoice.invoice_type == invoice_type)
    if status:
        q = q.filter(Invoice.status == status)
    if customer_id:
        q = q.filter(Invoice.customer_id == customer_id)
    total = q.count()
    items = q.order_by(desc(Invoice.date)).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "invoice_type": inv.invoice_type,
                "date": inv.date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "status": inv.status.value,
                "total": float(inv.total),
                "paid_amount": float(inv.paid_amount),
                "currency": inv.currency,
                "jurisdiction": inv.jurisdiction,
            }
            for inv in items
        ],
    }


@router.post("/invoices")
def create_invoice(req: InvoiceIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Generate invoice number
    count = db.query(Invoice).count()
    inv_num = f"INV-{date.today().year}-{count + 1:05d}"

    subtotal = Decimal(0)
    tax_total = Decimal(0)

    invoice = Invoice(
        invoice_number=inv_num,
        invoice_type=req.invoice_type,
        customer_id=uuid.UUID(req.customer_id) if req.customer_id else None,
        date=req.date,
        due_date=req.due_date,
        currency=req.currency,
        jurisdiction=req.jurisdiction,
        notes=req.notes,
        created_by=current_user.id,
    )
    db.add(invoice)
    db.flush()

    for item in req.items:
        qty = Decimal(str(item.quantity))
        price = Decimal(str(item.unit_price))
        line_total = qty * price
        subtotal += line_total

        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            description=item.description,
            quantity=qty,
            unit_price=price,
            total=line_total,
        )
        db.add(inv_item)

    invoice.subtotal = subtotal
    invoice.total = subtotal + tax_total
    db.commit()
    db.refresh(invoice)
    return {"id": str(invoice.id), "invoice_number": invoice.invoice_number, "total": float(invoice.total)}


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "invoice_type": inv.invoice_type,
        "date": inv.date.isoformat(),
        "due_date": inv.due_date.isoformat(),
        "status": inv.status.value,
        "subtotal": float(inv.subtotal),
        "tax_amount": float(inv.tax_amount),
        "total": float(inv.total),
        "paid_amount": float(inv.paid_amount),
        "currency": inv.currency,
        "jurisdiction": inv.jurisdiction,
        "notes": inv.notes,
        "items": [
            {
                "id": str(i.id),
                "description": i.description,
                "quantity": float(i.quantity),
                "unit_price": float(i.unit_price),
                "total": float(i.total),
            }
            for i in inv.items
        ],
    }


# ─── Dashboard / Reports ──────────────────────────────────────────────────────

@router.get("/dashboard")
def finance_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    # Total AR/AP
    ar_total = db.query(func.sum(Invoice.total - Invoice.paid_amount)).filter(
        Invoice.invoice_type == "AR",
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]),
    ).scalar() or 0

    ap_total = db.query(func.sum(Invoice.total - Invoice.paid_amount)).filter(
        Invoice.invoice_type == "AP",
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]),
    ).scalar() or 0

    overdue_count = db.query(func.count(Invoice.id)).filter(
        Invoice.status == InvoiceStatus.OVERDUE
    ).scalar() or 0

    # Revenue by month (last 6 months)
    revenue_by_month = db.query(
        func.date_trunc("month", Invoice.date).label("month"),
        func.sum(Invoice.total).label("total"),
    ).filter(
        Invoice.invoice_type == "AR",
        Invoice.status.in_([InvoiceStatus.PAID, InvoiceStatus.PARTIAL]),
    ).group_by("month").order_by("month").limit(6).all()

    return {
        "accounts_receivable": float(ar_total),
        "accounts_payable": float(ap_total),
        "overdue_invoices": overdue_count,
        "revenue_trend": [
            {"month": str(r.month)[:7], "total": float(r.total or 0)}
            for r in revenue_by_month
        ],
    }


# ─── Tax Rates ────────────────────────────────────────────────────────────────

@router.get("/tax-rates")
def list_tax_rates(
    jurisdiction: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(TaxRate).filter(TaxRate.is_active == True)
    if jurisdiction:
        q = q.filter(TaxRate.jurisdiction == jurisdiction)
    rates = q.all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "rate": float(r.rate),
            "jurisdiction": r.jurisdiction,
            "tax_type": r.tax_type,
        }
        for r in rates
    ]
