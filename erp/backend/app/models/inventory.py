from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Integer, Enum, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"


class MovementType(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    unit = Column(String(50), default="each")
    cost_price = Column(Numeric(18, 2))
    sale_price = Column(Numeric(18, 2))
    currency = Column(String(3), default="USD")
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    reorder_point = Column(Numeric(10, 3), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String(3))
    jurisdiction = Column(String(5), default="US")
    address = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movements = relationship("StockMovement", back_populates="warehouse")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_cost = Column(Numeric(18, 2))
    reference = Column(String(100))
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    warehouse = relationship("Warehouse", back_populates="movements")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(50), unique=True, nullable=False)
    vendor_name = Column(String(255), nullable=False)
    vendor_id = Column(UUID(as_uuid=True))
    status = Column(String(50), default="draft")
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date)
    total = Column(Numeric(18, 2), default=0)
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("PurchaseOrderItem", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    description = Column(String(500))
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(Numeric(18, 2), nullable=False)
    total = Column(Numeric(18, 2), nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
