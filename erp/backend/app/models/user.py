from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    FINANCE_MANAGER = "finance_manager"
    FINANCE_USER = "finance_user"
    HR_MANAGER = "hr_manager"
    HR_USER = "hr_user"
    CRM_MANAGER = "crm_manager"
    CRM_USER = "crm_user"
    COMPLIANCE_OFFICER = "compliance_officer"
    VIEWER = "viewer"


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id")),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id")),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id")),
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    jurisdiction = Column(String(5), default="US")  # US, UK, CA
    timezone = Column(String(50), default="UTC")
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))

    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # read, write, delete, approve

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
