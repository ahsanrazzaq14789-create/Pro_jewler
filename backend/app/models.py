from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from .database import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    full_name: Mapped[str]=mapped_column(String(160),default="")
    role: Mapped[str]=mapped_column(String(30),default="shop_admin")
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Shop(Base):
    __tablename__="shops"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(180))
    owner_name: Mapped[str]=mapped_column(String(160),default="")
    phone: Mapped[str]=mapped_column(String(50),default="")
    address: Mapped[str]=mapped_column(Text,default="")
    currency: Mapped[str]=mapped_column(String(8),default="PKR")
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Membership(Base):
    __tablename__="memberships"
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    shop_id: Mapped[int]=mapped_column(ForeignKey("shops.id"),index=True)
    role: Mapped[str]=mapped_column(String(30),default="shop_admin")
    __table_args__=(UniqueConstraint("user_id","shop_id"),)

class BusinessRecord(Base):
    __tablename__="business_records"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    shop_id: Mapped[int]=mapped_column(ForeignKey("shops.id"),index=True)
    module: Mapped[str]=mapped_column(String(40),index=True)
    title: Mapped[str]=mapped_column(String(240),default="")
    party: Mapped[str]=mapped_column(String(240),default="")
    details: Mapped[str]=mapped_column(Text,default="")
    metal: Mapped[str]=mapped_column(String(20),default="Gold")
    weight: Mapped[float]=mapped_column(Float,default=0)
    purity: Mapped[float]=mapped_column(Float,default=24)
    rate: Mapped[float]=mapped_column(Float,default=0)
    making: Mapped[float]=mapped_column(Float,default=0)
    discount: Mapped[float]=mapped_column(Float,default=0)
    amount: Mapped[float]=mapped_column(Float,default=0)
    paid: Mapped[float]=mapped_column(Float,default=0)
    balance: Mapped[float]=mapped_column(Float,default=0)
    status: Mapped[str]=mapped_column(String(40),default="Saved")
    reference: Mapped[str]=mapped_column(String(160),default="")
    deleted: Mapped[bool]=mapped_column(Boolean,default=False)
    version: Mapped[int]=mapped_column(Integer,default=1)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(primary_key=True)
    shop_id: Mapped[int]=mapped_column(Integer,index=True)
    user_id: Mapped[int]=mapped_column(Integer,index=True)
    action: Mapped[str]=mapped_column(String(80))
    entity_id: Mapped[str]=mapped_column(String(64),default="")
    detail: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
