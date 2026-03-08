# Personal Finance Forecast Calendar 🗓️💰

A lightweight, locally-hosted web application that helps you visualize your financial future. It combines your actual past transactions with your expected recurring bills to project your daily End-of-Day (EOD) balances on an interactive calendar.

Built with **FastAPI**, **SQLAlchemy** (SQLite), and **FullCalendar.js**.

## ✨ Features

* **Interactive Calendar View:** See your actual transactions, expected future expenses, and daily projected balances all in one place.
* **Smart Forecasting Engine:** Projects future balances by calculating the gap between your last reconciled date and your expected recurring transactions.
* **Auto-Deduplication:** Automatically hides expected recurring transactions if a matching actual transaction is entered within a ±10 day window. No double-counting!
* **Reconciliation System:** Anchor your timeline. Set a "Reconciled Up To" date to lock in your actuals and clean up historical projections.
* **Full CRUD Management:** Add, edit, and delete actual and recurring transactions directly from the calendar interface.
* **Multi-Account Support:** Easily switch between different accounts (Checking, Savings, Credit Cards) with automatic currency formatting.
* **Read-Only & Edit Modes:** Secure your daily view by defaulting to a read-only calendar. Append `?edit=true` to the URL to unlock management forms.

## 🛠️ Tech Stack

* **Backend:** Python 3, FastAPI, SQLAlchemy
* **Database:** SQLite (Zero configuration required)
* **Frontend:** HTML5, Vanilla JavaScript, Jinja2 Templates, FullCalendar.js

## 🚀 Getting Started

You don't need Docker or a heavy database server to run this. The app uses a simple SQLite file and a built-in Python environment.

### Prerequisites
* Python 3.10+ installed on your system.

### Installation & Running

1. **Clone the repository:**
   ```bash
   git clone https://github.com/handstand2002/finance-calendar.git
   cd finance-calendar
   ```

2. **Run the startup script:**
We've included a handy bash script that creates a virtual environment, installs dependencies, and boots the server.
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. **Open your browser:**
Navigate to http://localhost:8000/calendar/1?edit=true to view the app in Edit Mode.

*Note: On your very first run, you may need to use a SQLite viewer (like DB Browser for SQLite) to add a dummy account into the `accounts` table so the dropdown has something to load!*

## 📖 How It Works

### The Forecasting Logic

The Python forecasting engine reads your `transactions` (actuals) and `recurring_tx` (expectations).

1. It calculates your starting balance based on actuals prior to 30 days ago.
2. It projects your recurring rules forward into the future.
3. **The ±10 Day Rule:** If you expect a $1,200 Rent payment on the 1st, but you manually enter an actual $1,200 Rent payment on the 3rd linked to that recurring rule, the engine will automatically suppress the projection for the 1st.

### Reconciling

If you fall behind on entering actual transactions, your historical calendar might look messy with old "expected" projections.

1. Log into your real-world bank account.
2. Ensure your actual transactions in the app match your bank up to today.
3. Click **Reconcile Account** and enter today's date.
4. The engine will instantly wipe out all unconfirmed projections prior to that date, assuming your actuals are the absolute truth.

## 📂 Project Structure

```text
├── start.sh              # 1-click startup script (creates venv & runs app)
├── migrate.py            # Utility script to migrate data from Postgres to SQLite
├── main.py               # FastAPI application, endpoints, and forecast engine
├── database.py           # SQLite connection setup
├── models.py             # SQLAlchemy ORM definitions
├── schemas.py            # Pydantic validation models
├── templates/
│   └── calendar.html     # The frontend UI and FullCalendar implementation
└── data/                 
    └── finance.db        # Auto-generated SQLite database (ignored in git)

```
