#!/bin/bash
set -e

echo "Setting up UrbanMind..."
cp .env.example .env
docker-compose pull
docker-compose build
docker-compose up -d redis mqtt
sleep 3
docker-compose up -d api
until curl -sf http://localhost:8000/health >/dev/null; do
  echo "Waiting for API health..."
  sleep 2
done
python3 scripts/seed_intersections.py
docker-compose up -d cv_worker simulator frontend
echo "UrbanMind running at http://localhost:3000"
echo "API docs at http://localhost:8000/docs"
