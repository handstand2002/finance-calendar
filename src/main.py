from typing import Optional
import calendar
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date, timedelta
from decimal import Decimal

import models, schemas
from database import engine, get_db

app = FastAPI(title="Finance Forecast API")
# Create the SQLite database file and all tables if they don't exist yet
models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

# ==========================================
# PYTHON FORECAST ENGINE
# ==========================================
def generate_forecast(db: Session, account_id: int):
    today = date.today()
    start_date = today - timedelta(days=30)
    end_date = today + timedelta(days=60)

    # 1. Get latest recon date
    recon_date = db.query(func.max(models.Recon.date)).filter(
        models.Recon.account == account_id, 
        models.Recon.complete == True
    ).scalar()
    if not recon_date:
        recon_date = today

    # 2. Fetch all required data into memory
    actuals = db.query(models.Transaction).filter(
        models.Transaction.account == account_id, 
        models.Transaction.date <= end_date
    ).all()
    
    recurring = db.query(models.RecurringTx).filter(
        models.RecurringTx.account == account_id, 
        models.RecurringTx.active == True
    ).all()

    # Helper function for exclusion logic (+/- 10 days)
    def has_match(rtx_id, target_date):
        window_start = target_date - timedelta(days=10)
        window_end = target_date + timedelta(days=10)
        for t in actuals:
            if t.recurring_tx == rtx_id and window_start <= t.date <= window_end:
                return True
        return False

    # 3. Calculate Opening Balance (Prior to T-30)
    base_opening = sum((t.amount for t in actuals if t.date < start_date), Decimal('0.0'))
    
    gap_opening = Decimal('0.0')
    curr_gap_day = recon_date + timedelta(days=1)
    while curr_gap_day < start_date:
        # Determine the maximum valid day for the current month in the loop
        _, days_in_month = calendar.monthrange(curr_gap_day.year, curr_gap_day.month)
        
        for rtx in recurring:
            # Snap to the end of the month if the day_of_month is too high
            effective_day = min(rtx.day_of_month, days_in_month)
            
            if effective_day == curr_gap_day.day:
                if not has_match(rtx.id, curr_gap_day):
                    gap_opening += rtx.amount
        curr_gap_day += timedelta(days=1)
        
    opening_balance = base_opening + gap_opening

    # 4. Process Daily Data
    daily_data = {}
    curr = start_date
    while curr <= end_date:
        daily_data[curr] = {'expense': Decimal('0.0'), 'income': Decimal('0.0'), 'txs': []}
        curr += timedelta(days=1)

    # Apply Actuals
    for t in actuals:
        if start_date <= t.date <= end_date:
            if t.amount < 0:
                daily_data[t.date]['expense'] += t.amount
            else:
                daily_data[t.date]['income'] += t.amount
            desc = t.description or 'Uncategorized'
            
            # Use a dictionary instead of a string
            daily_data[t.date]['txs'].append({
                "type": "TX",
                "id": t.id,
                "amount": float(t.amount),
                "desc": desc
            })

    # Apply Projections
    curr_proj_day = start_date
    while curr_proj_day <= end_date:
        if curr_proj_day > recon_date:
            _, days_in_month = calendar.monthrange(curr_proj_day.year, curr_proj_day.month)
            for rtx in recurring:
                effective_day = min(rtx.day_of_month, days_in_month)
                if effective_day == curr_proj_day.day:
                    if not has_match(rtx.id, curr_proj_day):
                        if rtx.amount < 0:
                            daily_data[curr_proj_day]['expense'] += rtx.amount
                        else:
                            daily_data[curr_proj_day]['income'] += rtx.amount
                        
                        # Use a dictionary instead of a string
                        daily_data[curr_proj_day]['txs'].append({
                            "type": "EXP",
                            "recurring_tx_id": rtx.id,
                            "amount": float(rtx.amount),
                            "desc": rtx.name
                        })
        curr_proj_day += timedelta(days=1)

    # Calculate Running Totals
    results = []
    running_eod = opening_balance
    curr = start_date
    while curr <= end_date:
        stats = daily_data[curr]
        running_eod += (stats['expense'] + stats['income'])
        results.append({
            "report_date": curr,
            "eod_balance": float(running_eod),
            "transactions": stats['txs'] # Now passing the raw list of dicts
        })
        curr += timedelta(days=1)
        
    return results

# ==========================================
# ENDPOINTS
# ==========================================
@app.get("/api/accounts")
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    return [{"id": a.id, "name": a.name} for a in accounts]

@app.post("/transactions/", response_model=schemas.TransactionResponse)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_tx = models.Transaction(**tx.model_dump())
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

@app.put("/transactions/{tx_id}", response_model=schemas.TransactionResponse)
def update_transaction(tx_id: int, tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not db_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db_tx.date = tx.date
    db_tx.amount = tx.amount
    db_tx.description = tx.description
    db_tx.account = tx.account
    db_tx.recurring_tx = tx.recurring_tx
    
    db.commit()
    db.refresh(db_tx)
    return db_tx

@app.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    db_tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not db_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(db_tx)
    db.commit()
    return {"status": "success", "message": "Transaction deleted"}

@app.post("/recurring/", response_model=schemas.RecurringTxResponse)
def create_recurring(rtx: schemas.RecurringTxCreate, db: Session = Depends(get_db)):
    db_rtx = models.RecurringTx(**rtx.model_dump())
    db.add(db_rtx)
    db.commit()
    db.refresh(db_rtx)
    return db_rtx

@app.get("/api/calendar-events/{account_id}")
def get_calendar_events(account_id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    currency_code = account.ccy if account and account.ccy else "USD"

    forecast_data = generate_forecast(db, account_id)
    
    events = []
    for row in forecast_data:
        date_str = row["report_date"].isoformat()
        
        # 1. Transaction Events (Expected and Actual) - SORT ORDER 1
        for tx in row["transactions"]:
            is_projection = tx["type"] == "EXP"
            tx["currency"] = currency_code
            
            events.append({
                "title": tx["desc"],
                "start": date_str,
                "allDay": True,
                "color": "#ffc107" if is_projection else "#007bff",
                "textColor": "#000" if is_projection else "#fff",
                "sortOrder": 1,  # Force to the top
                "extendedProps": tx 
            })

        # 2. EOD Event - SORT ORDER 2
        events.append({
            "title": "EOD",
            "start": date_str,
            "allDay": True,
            "color": "#28a745" if row["eod_balance"] >= 0 else "#dc3545",
            "sortOrder": 2,  # Force to the bottom
            "extendedProps": { "amount": row["eod_balance"], "currency": currency_code, "type": "eod" }
        })
            
    return events

@app.get("/calendar/{account_id}", response_class=HTMLResponse)
def view_calendar(request: Request, account_id: int, edit: Optional[str] = None):
    # Check if the query param exactly equals "true"
    is_edit_mode = (edit == "true")
    
    return templates.TemplateResponse(
        "calendar.html", 
        {"request": request, "account_id": account_id, "is_edit": is_edit_mode}
    )

# Add this endpoint to fetch all rules for the selected account
@app.get("/recurring/account/{account_id}", response_model=list[schemas.RecurringTxResponse])
def get_recurring_by_account(account_id: int, db: Session = Depends(get_db)):
    return db.query(models.RecurringTx).filter(models.RecurringTx.account == account_id).order_by(models.RecurringTx.day_of_month).all()

# Add this endpoint to update an existing rule
@app.put("/recurring/{rtx_id}", response_model=schemas.RecurringTxResponse)
def update_recurring(rtx_id: int, rtx: schemas.RecurringTxCreate, db: Session = Depends(get_db)):
    db_rtx = db.query(models.RecurringTx).filter(models.RecurringTx.id == rtx_id).first()
    if not db_rtx:
        raise HTTPException(status_code=404, detail="Recurring Transaction not found")
    
    db_rtx.name = rtx.name
    db_rtx.amount = rtx.amount
    db_rtx.day_of_month = rtx.day_of_month
    db_rtx.active = rtx.active
    
    db.commit()
    db.refresh(db_rtx)
    return db_rtx

# Add this endpoint to delete a rule entirely
@app.delete("/recurring/{rtx_id}")
def delete_recurring(rtx_id: int, db: Session = Depends(get_db)):
    db_rtx = db.query(models.RecurringTx).filter(models.RecurringTx.id == rtx_id).first()
    if not db_rtx:
        raise HTTPException(status_code=404, detail="Recurring Transaction not found")
    
    db.delete(db_rtx)
    db.commit()
    return {"status": "success", "message": "Recurring transaction deleted"}

@app.post("/recon/")
def create_recon(recon: schemas.ReconCreate, db: Session = Depends(get_db)):
    db_recon = models.Recon(
        account=recon.account,
        date=recon.date,
        complete=True
    )
    db.add(db_recon)
    db.commit()
    return {"status": "success", "message": f"Account reconciled up to {recon.date}"}
