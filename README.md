# Dynamic AI Traffic Flow Optimizer & Emergency Grid

This repository contains a runnable Python prototype for an intelligent traffic
management system that combines:

- Real-time computer vision ingest for lane-level traffic density estimation
- Adaptive signal timing based on live traffic pressure
- Emergency green-corridor orchestration for ambulances and fire services
- A small JSON HTTP API for simulation and integration testing

## System design

### 1. Computer vision ingest

`VisionTrafficAnalyzer` accepts streaming detections from road-side cameras. Each
detection is mapped to a lane and converted into:

- vehicle count
- heavy-vehicle count
- occupancy ratio
- average speed
- queue length estimate
- emergency-vehicle presence

These features are fused into a per-lane pressure score.

### 2. Dynamic signal control

`AdaptiveSignalController` aggregates lane pressures into signal phases such as
`north_south` and `east_west`. It then distributes the usable cycle time across
phases while respecting:

- minimum green time
- maximum green time
- yellow and all-red lost time

High-pressure approaches automatically receive larger green windows.

### 3. Emergency grid / green corridor

`EmergencyCorridorManager` accepts an emergency route with intersection ETAs and
required phases. It preempts normal timing plans by:

- reserving green time on the route
- compressing conflicting phases to their minimum safe duration
- annotating each intersection with a preemption command and activation window

## Project layout

- `src/traffic_ai/models.py`: shared data structures
- `src/traffic_ai/vision.py`: computer vision to traffic metrics conversion
- `src/traffic_ai/optimizer.py`: adaptive signal timing engine
- `src/traffic_ai/network.py`: network-level orchestration and emergency logic
- `src/traffic_ai/api.py`: JSON HTTP server
- `src/traffic_ai/demo.py`: sample simulation run
- `tests/`: unit tests

## Run the demo

```bash
PYTHONPATH=src python -m traffic_ai.demo
```

## Run the API

```bash
PYTHONPATH=src python -m traffic_ai.api
```

The server listens on `http://127.0.0.1:8080`.

### Example: vision update

```bash
curl -X POST http://127.0.0.1:8080/vision/update \
  -H "Content-Type: application/json" \
  -d '{
    "intersection_id": "J1",
    "detections": [
      {"lane_id": "J1_N", "label": "car", "bbox_area_ratio": 0.05, "speed_kph": 12},
      {"lane_id": "J1_N", "label": "ambulance", "bbox_area_ratio": 0.08, "speed_kph": 35},
      {"lane_id": "J1_E", "label": "truck", "bbox_area_ratio": 0.07, "speed_kph": 8}
    ]
  }'
```

### Example: emergency corridor request

```bash
curl -X POST http://127.0.0.1:8080/emergency/corridor \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "AMB-12",
    "vehicle_type": "ambulance",
    "route": [
      {"intersection_id": "J1", "required_phase": "north_south", "eta_seconds": 12},
      {"intersection_id": "J2", "required_phase": "north_south", "eta_seconds": 34},
      {"intersection_id": "J3", "required_phase": "east_west", "eta_seconds": 58}
    ]
  }'
```

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Dashboard deployment

The dashboard frontend lives in `urbanmind/frontend` and the FastAPI backend
lives in `urbanmind/backend`.

### Config files included

- `render.yaml`: Render Blueprint for frontend, backend, and Redis-compatible Key Value
- `urbanmind/frontend/vercel.json`: Vercel config for the Vite frontend
- `urbanmind/vercel.json`: Vercel config for the FastAPI backend bundle
- `urbanmind/frontend/.env.example`: frontend deploy variables
- `urbanmind/backend/.env.example`: backend deploy variables

### Important Vercel note

Vercel Functions do not support acting as a WebSocket server. This repo now
supports polling mode for the dashboard so the backend can still run on Vercel,
but live updates on Vercel are HTTP polling, not persistent WebSockets. Render
supports the backend's current WebSocket endpoint.

### Option 1: frontend on Vercel, backend on Render

This is the best fit if you want the current real-time WebSocket behavior.

1. Push the repo to GitHub.
2. In Vercel, create a project with root directory `urbanmind/frontend`.
3. Vercel will use `urbanmind/frontend/vercel.json`.
4. Set:
   - `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`
   - `VITE_WS_URL=wss://<your-render-backend>.onrender.com/ws/live`
   - `VITE_LIVE_TRANSPORT=websocket`
5. In Render, create a Web Service with root directory `urbanmind`.
6. Use:
   - Build command: `pip install -r backend/requirements.txt`
   - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
7. Set backend variables:
   - `BACKEND_CORS_ORIGINS=https://<your-vercel-frontend>.vercel.app`
   - `REDIS_URL=<your-redis-url>`
8. Deploy and test `https://<your-render-backend>.onrender.com/health`.

### Option 2: frontend and backend both on Render

This supports the current WebSocket flow without any frontend changes.

1. Push the repo to GitHub.
2. In Render, create a new Blueprint from this repository.
3. Render will detect `render.yaml` at the repo root.
4. Review the three resources:
   - `urbanmind-frontend`
   - `urbanmind-backend`
   - `urbanmind-cache`
5. Fill in prompted values for `BACKEND_CORS_ORIGINS`, `VITE_API_BASE_URL`, and `VITE_WS_URL`.
6. Set:
   - `BACKEND_CORS_ORIGINS=https://<your-render-frontend>.onrender.com`
   - `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`
   - `VITE_WS_URL=wss://<your-render-backend>.onrender.com/ws/live`
   - `VITE_LIVE_TRANSPORT=websocket`
7. Apply the Blueprint and let Render provision all services.

### Option 3: frontend and backend both on Vercel

This works only in polling mode.

1. Push the repo to GitHub.
2. Create one Vercel project for the frontend with root directory `urbanmind/frontend`.
3. Create a second Vercel project for the backend with root directory `urbanmind`.
4. The backend project uses:
   - `urbanmind/app.py`
   - `urbanmind/requirements.txt`
   - `urbanmind/vercel.json`
5. Set backend variables:
   - `BACKEND_CORS_ORIGINS=https://<your-vercel-frontend>.vercel.app`
   - `REDIS_URL=<your-redis-url>`
6. Set frontend variables:
   - `VITE_API_BASE_URL=https://<your-vercel-backend>.vercel.app`
   - `VITE_LIVE_TRANSPORT=polling`
   - `VITE_POLL_INTERVAL_MS=5000`
7. Leave `VITE_WS_URL` unset or empty for the Vercel-only setup.
8. Deploy both projects.

### Quick Vercel CLI deploy

Frontend:

```bash
cd urbanmind/frontend
npx vercel
```

Backend:

```bash
cd urbanmind
npx vercel
```

### Push to GitHub

```bash
git init -b main
git remote add origin https://github.com/Anurag-M1/UrbanMind.git
git add .
git commit -m "Initial deploy-ready setup"
git push -u origin main
```

---

Designed and Developed By Anurag Singh
