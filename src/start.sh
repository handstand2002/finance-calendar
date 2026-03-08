#!/bin/bash

# Exit immediately if a command fails
set -e

# 1. Change to the directory where this script is located, 
# regardless of where the user is calling it from.
cd "$(dirname "$0")"

echo "🚀 Starting Finance Forecast setup..."

# 2. Terminate the server if it's already running
echo "🛑 Checking for existing server instances..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "   Found existing instance. Terminating..."
    pkill -f "uvicorn main:app"
    sleep 2 # Give it a moment to shut down gracefully
    
    # Force kill if it's being stubborn, but suppress the error if it's already dead
    pkill -9 -f "uvicorn main:app" 2>/dev/null || true
else
    echo "   No existing instances found."
fi

# 3. Create a virtual environment if it doesn't exist yet
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# 4. Activate the virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# 5. Install requirements quietly to avoid cluttering the terminal
echo "⬇️ Verifying dependencies..."
pip install --upgrade pip --quiet
pip install fastapi uvicorn sqlalchemy jinja2 --quiet

# 6. Create the data folder for the SQLite database and logs
if [ ! -d "data" ]; then
    echo "📁 Creating 'data' directory..."
    mkdir data
fi

# 7. Export environment variables
export DATABASE_URL="sqlite:///./data/finance.db"

# 8. Start the server in the background
echo "🌟 Starting the web server in the background..."
echo "📝 Logs are being written to: $(pwd)/data/log.txt"
echo "👉 Open your browser to: http://localhost:8000/calendar/1?edit=true"

# Use nohup to decouple the process from the terminal, redirecting all output to the log file
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > data/log.txt 2>&1 &

# Print the Process ID of the server we just started
echo "✅ Server is running! (PID: $!)"
