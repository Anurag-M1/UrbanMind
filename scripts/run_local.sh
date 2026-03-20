#!/bin/bash
# UrbanMind — Local Runner (No Docker)
# This script installs required system dependencies via Homebrew,
# sets up a Python virtual environment, installs Node modules,
# and runs all four UrbanMind services in the background.

set -e

echo "============================================="
echo " UrbanMind Local Runner (No Docker)"
echo "============================================="

# 1. Add Homebrew paths
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"

echo "[1/6] Installing system dependencies (Redis, Mosquitto, ffmpeg, node)..."
# We will use 'brew install' individually in case they already exist
brew list redis &>/dev/null || brew install redis
brew list mosquitto &>/dev/null || brew install mosquitto
brew list ffmpeg &>/dev/null || brew install ffmpeg
brew list node &>/dev/null || brew install node

echo "[2/6] Starting background infrastructure..."
# Stop brew services if they are already running to avoid port conflicts, then start them manually
brew services stop redis 2>/dev/null || true
brew services stop mosquitto 2>/dev/null || true

# Start Redis
redis-server --daemonize yes

# Start Mosquitto with our custom config
# Create data dirs first
mkdir -p data/mosquitto/config data/mosquitto/data data/mosquitto/log
mosquitto -c mosquitto.conf -d

echo "[3/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "Installing Backend dependencies..."
pip install -r backend/requirements.txt
echo "Installing CV Engine dependencies..."
pip install -r cv-engine/requirements.txt
echo "Installing Simulator dependencies..."
pip install -r simulator/requirements.txt

# Create .env if missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

echo "[4/6] Exporting environment variables for localhost..."
export REDIS_URL="redis://localhost:6379/1"
export MQTT_HOST="localhost"
export API_URL="http://localhost:8000"
export DEFAULT_EW_GREEN=45
export DEFAULT_NS_GREEN=45

echo "[5/6] Starting microservices..."

# 5a. Backend API
echo "  -> Starting Backend (FastAPI on port 8000)..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Sleep briefly to let the API start up before seeding
sleep 3

# Seed intersections
echo "  -> Seeding database..."
python scripts/seed_intersections.py

# 5b. CV Engine Worker
echo "  -> Starting CV Engine (YOLOv8 worker)..."
cd cv-engine
python detector.py > ../cv-engine.log 2>&1 &
CV_PID=$!
cd ..

# 5c. Simulator
echo "  -> Starting Traffic Simulator..."
cd simulator
python traffic_sim.py > ../simulator.log 2>&1 &
SIM_PID=$!
cd ..

# 5d. Frontend
echo "[6/6] Starting Frontend (React/Vite on port 3000)..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "============================================="
echo " UrbanMind is now running locally!"
echo "============================================="
echo " Dashboard: http://localhost:3000"
echo " API Docs:  http://localhost:8000/docs"
echo ""
echo " Logs are being written to:"
echo "   - backend.log"
echo "   - cv-engine.log"
echo "   - simulator.log"
echo "   - frontend.log"
echo ""
echo " To stop all services, run:"
echo " kill $BACKEND_PID $CV_PID $SIM_PID $FRONTEND_PID; pkill redis-server; pkill mosquitto"
echo "============================================="

# Keep script running to hold the process tree (optional, uncomment to block)
# wait
