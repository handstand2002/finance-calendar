from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Boolean
from database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ccy = Column(String, nullable=True)

class Recon(Base):
    __tablename__ = "recon"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    complete = Column(Boolean, default=False, nullable=False)
    account = Column(Integer, ForeignKey("accounts.id"), nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    account = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    description = Column(String, nullable=True)
    recurring_tx = Column(Integer, ForeignKey("recurring_tx.id"), nullable=True)

class RecurringTx(Base):
    __tablename__ = "recurring_tx"
    id = Column(Integer, primary_key=True, index=True)
    account = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    day_of_month = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
