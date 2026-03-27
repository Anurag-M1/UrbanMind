#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════"
echo "  UrbanMind — AI Traffic Optimizer Setup"
echo "  India Innovates 2026 · Bharat Mandapam"
echo "═══════════════════════════════════════════════════"
echo ""

# Copy env if needed
if [ ! -f .env ]; then
  echo "→ Creating .env from .env.example..."
  cp .env.example .env
fi

# Create uploads dir
mkdir -p backend/uploads

echo ""
echo "→ Building Docker containers..."
docker-compose build --no-cache

echo ""
echo "→ Starting Redis + MQTT..."
docker-compose up -d redis mqtt
sleep 4

echo ""
echo "→ Starting API server..."
docker-compose up -d api
sleep 6

echo ""
echo "→ Seeding intersection data..."
docker-compose exec api python scripts_seed.py || echo "  (Seed will run on startup via DEMO_MODE)"

echo ""
echo "→ Starting frontend..."
docker-compose up -d frontend

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ UrbanMind is running!"
echo ""
echo "  Dashboard  → http://localhost:3000"
echo "  API Docs   → http://localhost:8000/docs"
echo "  Health     → http://localhost:8000/health"
echo ""
echo "  Demo Steps:"
echo "   1. Open http://localhost:3000"
echo "   2. Watch the 3D city on Overview page"
echo "   3. Upload a traffic video on Video Analysis"
echo "   4. Click Dispatch Ambulance on Emergency"
echo "   5. View live Analytics dashboard"
echo "═══════════════════════════════════════════════════"
