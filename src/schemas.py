from pydantic import BaseModel
from datetime import date
from typing import Optional
from decimal import Decimal

class TransactionBase(BaseModel):
    date: date
    amount: Decimal
    account: int
    description: Optional[str] = None
    recurring_tx: Optional[int] = None

class TransactionCreate(TransactionBase): pass

class TransactionResponse(TransactionBase):
    id: int
    class Config:
        from_attributes = True

class RecurringTxBase(BaseModel):
    account: int
    name: str
    amount: Decimal
    day_of_month: int
    active: bool = True

class RecurringTxCreate(RecurringTxBase): pass

class RecurringTxResponse(RecurringTxBase):
    id: int
    class Config:
        from_attributes = True

class ReconCreate(BaseModel):
    account: int
    date: date
