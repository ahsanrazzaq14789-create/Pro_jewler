from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
class LoginIn(BaseModel):
    email: str
    password: str
class RegisterIn(BaseModel):
    email: str
    password: str=Field(min_length=10)
    full_name: str=""
    shop_name: str
    phone: str=""
class ShopIn(BaseModel):
    name: str
    owner_name: str=""
    phone: str=""
    address: str=""
    currency: str="PKR"
class RecordIn(BaseModel):
    id: str
    module: str
    title: str=""
    party: str=""
    details: str=""
    metal: str="Gold"
    weight: float=0
    purity: float=24
    rate: float=0
    making: float=0
    discount: float=0
    amount: float=0
    paid: float=0
    balance: float=0
    status: str="Saved"
    reference: str=""
    version: int=1
class RecordOut(RecordIn):
    shop_id: int
    deleted: bool=False
    updated_at: datetime
    created_at: datetime
    class Config: from_attributes=True
class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    class Config: from_attributes=True
