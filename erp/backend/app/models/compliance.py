from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text,
    Numeric, Integer, Enum, Date, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class SanctionListSource(str, enum.Enum):
    OFAC_SDN = "OFAC_SDN"           # US Treasury SDN
    OFAC_CONSOLIDATED = "OFAC_CONS"  # US OFAC Consolidated
    UN = "UN"                         # UN Security Council
    EU = "EU"                         # European Union
    UK_HMT = "UK_HMT"               # UK HM Treasury
    CANADA_SEMA = "CANADA_SEMA"     # Canada SEMA


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SanctionList(Base):
    __tablename__ = "sanction_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Enum(SanctionListSource), nullable=False)
    last_updated = Column(DateTime(timezone=True))
    entry_count = Column(Integer, default=0)
    checksum = Column(String(64))
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entities = relationship("SanctionedEntity", back_populates="sanction_list")


class SanctionedEntity(Base):
    __tablename__ = "sanctioned_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sanction_list_id = Column(UUID(as_uuid=True), ForeignKey("sanction_lists.id"), nullable=False)
    external_id = Column(String(100))
    entity_type = Column(String(50))  # individual, entity, vessel, aircraft
    names = Column(JSONB)              # primary + aliases
    addresses = Column(JSONB)
    nationalities = Column(JSONB)
    dates_of_birth = Column(JSONB)
    id_numbers = Column(JSONB)         # passports, national IDs
    programs = Column(JSONB)           # sanction programs
    remarks = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sanction_list = relationship("SanctionList", back_populates="entities")


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)  # sanctions_match, kyc_fail, regulatory_change
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    entity_type = Column(String(50))   # customer, employee, vendor
    entity_id = Column(UUID(as_uuid=True))
    match_score = Column(Float)
    matched_entity_id = Column(UUID(as_uuid=True), ForeignKey("sanctioned_entities.id"))
    jurisdiction = Column(String(5))
    metadata = Column(JSONB)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    matched_entity = relationship("SanctionedEntity")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RegulatoryUpdate(Base):
    __tablename__ = "regulatory_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction = Column(String(5), nullable=False)
    category = Column(String(100), nullable=False)  # GDPR, SOX, HIPAA, CASL, etc.
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    source_url = Column(String(1000))
    effective_date = Column(Date)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM)
    is_read = Column(Boolean, default=False)
    requires_action = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KYCRecord(Base):
    __tablename__ = "kyc_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, approved, rejected
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    verification_method = Column(String(100))
    documents = Column(JSONB)          # list of verified documents
    sanctions_checked = Column(Boolean, default=False)
    sanctions_checked_at = Column(DateTime(timezone=True))
    pep_checked = Column(Boolean, default=False)  # Politically Exposed Person
    aml_score = Column(Float)
    notes = Column(Text)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    risk_score = Column(Float, nullable=False)
    factors = Column(JSONB)
    jurisdiction = Column(String(5))
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assessed_at = Column(DateTime(timezone=True), server_default=func.now())
    next_review_at = Column(DateTime(timezone=True))
    notes = Column(Text)
