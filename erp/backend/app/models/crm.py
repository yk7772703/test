from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Enum, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class CustomerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class OpportunityStage(str, enum.Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_number = Column(String(50), unique=True, nullable=False)
    customer_type = Column(Enum(CustomerType), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    industry = Column(String(100))
    country = Column(String(3))
    jurisdiction = Column(String(5), default="US")
    address = Column(JSONB)
    tax_id = Column(String(50))
    credit_limit = Column(Numeric(18, 2))
    payment_terms = Column(Integer, default=30)  # days
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    is_sanctioned = Column(Boolean, default=False)
    kyc_status = Column(String(50), default="pending")
    risk_level = Column(String(20), default="low")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contacts = relationship("Contact", back_populates="customer")
    opportunities = relationship("Opportunity", back_populates="customer")
    kyc_records = relationship("KYCRecord", back_populates="customer")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="contacts")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    stage = Column(Enum(OpportunityStage), default=OpportunityStage.LEAD)
    value = Column(Numeric(18, 2))
    currency = Column(String(3), default="USD")
    probability = Column(Numeric(5, 2))  # 0-100%
    expected_close_date = Column(Date)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="opportunities")
    activities = relationship("Activity", back_populates="opportunity")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    activity_type = Column(String(50))  # call, email, meeting, task
    subject = Column(String(500), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="activities")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    title = Column(String(500), nullable=False)
    value = Column(Numeric(18, 2))
    currency = Column(String(3), default="USD")
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50), default="draft")
    jurisdiction = Column(String(5), default="US")
    terms = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
