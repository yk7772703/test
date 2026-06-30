from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text,
    Numeric, Integer, Enum, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CHECK = "check"
    CASH = "cash"
    ACH = "ach"
    WIRE = "wire"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    currency = Column(String(3), default="USD")
    jurisdiction = Column(String(5), default="US")
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    balance = Column(Numeric(18, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("Account", remote_side=[id])
    journal_lines = relationship("JournalLine", back_populates="account")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_number = Column(String(50), unique=True, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    reference = Column(String(100))
    jurisdiction = Column(String(5), default="US")
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(18, 6), default=1.0)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime(timezone=True))
    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lines = relationship("JournalLine", back_populates="journal_entry")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    debit = Column(Numeric(18, 2), default=0)
    credit = Column(Numeric(18, 2), default=0)
    description = Column(Text)
    tax_rate_id = Column(UUID(as_uuid=True), ForeignKey("tax_rates.id"))

    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_lines")
    tax_rate = relationship("TaxRate")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_type = Column(String(20), default="AR")  # AR=receivable, AP=payable
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    currency = Column(String(3), default="USD")
    subtotal = Column(Numeric(18, 2), default=0)
    tax_amount = Column(Numeric(18, 2), default=0)
    total = Column(Numeric(18, 2), default=0)
    paid_amount = Column(Numeric(18, 2), default=0)
    jurisdiction = Column(String(5), default="US")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    items = relationship("InvoiceItem", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 3), default=1)
    unit_price = Column(Numeric(18, 2), nullable=False)
    tax_rate_id = Column(UUID(as_uuid=True), ForeignKey("tax_rates.id"))
    tax_amount = Column(Numeric(18, 2), default=0)
    total = Column(Numeric(18, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    tax_rate = relationship("TaxRate")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    invoice = relationship("Invoice", back_populates="payments")


class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    rate = Column(Numeric(6, 4), nullable=False)  # e.g., 0.0825 for 8.25%
    jurisdiction = Column(String(5), nullable=False)
    tax_type = Column(String(50))  # VAT, GST, HST, PST, sales_tax
    is_active = Column(Boolean, default=True)
    effective_from = Column(Date)
    effective_to = Column(Date)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    total_amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="USD")
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lines = relationship("BudgetLine", back_populates="budget")


class BudgetLine(Base):
    __tablename__ = "budget_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    period = Column(Integer, nullable=False)  # 1-12 for month
    planned_amount = Column(Numeric(18, 2), nullable=False)
    actual_amount = Column(Numeric(18, 2), default=0)

    budget = relationship("Budget", back_populates="lines")


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(3), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    symbol = Column(String(5))
    is_active = Column(Boolean, default=True)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(18, 6), nullable=False)
    date = Column(Date, nullable=False)
    source = Column(String(50))
