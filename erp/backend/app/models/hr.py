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


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERN = "intern"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    cost_center = Column(String(50))
    jurisdiction = Column(String(5), default="US")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("Department", remote_side=[id])
    employees = relationship("Employee", foreign_keys="Employee.department_id", back_populates="department")


class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    min_salary = Column(Numeric(18, 2))
    max_salary = Column(Numeric(18, 2))
    is_active = Column(Boolean, default=True)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"))
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    employment_type = Column(Enum(EmploymentType), default=EmploymentType.FULL_TIME)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    salary = Column(Numeric(18, 2))
    salary_currency = Column(String(3), default="USD")
    jurisdiction = Column(String(5), default="US")  # US, UK, CA
    # US specific
    ssn_last4 = Column(String(4))
    federal_tax_withholding = Column(JSONB)
    # UK specific
    ni_number = Column(String(20))
    # Canada specific
    sin_last3 = Column(String(3))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    department = relationship("Department", foreign_keys=[department_id], back_populates="employees")
    position = relationship("Position")
    manager = relationship("Employee", remote_side=[id])
    payrolls = relationship("Payroll", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")


class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    gross_pay = Column(Numeric(18, 2), nullable=False)
    net_pay = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="USD")
    jurisdiction = Column(String(5), default="US")
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    payment_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="payrolls")
    items = relationship("PayrollItem", back_populates="payroll")


class PayrollItem(Base):
    __tablename__ = "payroll_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_id = Column(UUID(as_uuid=True), ForeignKey("payrolls.id"), nullable=False)
    item_type = Column(String(50), nullable=False)  # base_salary, overtime, bonus, federal_tax, fica, etc.
    description = Column(String(255))
    amount = Column(Numeric(18, 2), nullable=False)
    is_deduction = Column(Boolean, default=False)

    payroll = relationship("Payroll", back_populates="items")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)  # annual, sick, maternity, paternity, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Numeric(4, 1))
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    reason = Column(Text)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="leave_requests")


class Benefit(Base):
    __tablename__ = "benefits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    benefit_type = Column(String(50))  # health, dental, vision, retirement, etc.
    jurisdiction = Column(String(5), default="US")
    employer_contribution = Column(Numeric(18, 2))
    employee_contribution = Column(Numeric(18, 2))
    is_active = Column(Boolean, default=True)


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    review_period = Column(String(20))
    rating = Column(Integer)  # 1-5
    comments = Column(Text)
    goals = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
