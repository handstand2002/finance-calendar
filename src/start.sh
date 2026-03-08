#!/bin/bash

# Exit immediately if a command fails
set -e

echo "🚀 Starting Finance Forecast setup..."

# 1. Create a virtual environment if it doesn't exist yet
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# 2. Activate the virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# 3. Install requirements
echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy jinja2

# 4. Create the data folder for the SQLite database
if [ ! -d "data" ]; then
    echo "📁 Creating 'data' directory for SQLite..."
    mkdir data
fi

# 5. Export environment variables
export DATABASE_URL="sqlite:///./data/finance.db"

# 6. Start the server (with reload enabled for easy development)
echo "🌟 Starting the web server..."
echo "👉 Open your browser to: http://localhost:8000/calendar/1?edit=true"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
