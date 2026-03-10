# UrbanMind

UrbanMind is an edge-deployed AI traffic management platform for adaptive signal timing, emergency corridor pre-emption, and live city-scale monitoring.

## Architecture

```text
                        +----------------------------+
                        |    React Dashboard         |
                        |  map, KPIs, live alerts    |
                        +-------------+--------------+
                                      |
                                WebSocket / REST
                                      |
                        +-------------v--------------+
                        |      FastAPI Backend       |
                        | Redis cache + MQTT ingest  |
                        +------+------+--------------+
                               |      |
                    MQTT state |      | MQTT command / override
                               |      |
        +----------------------v--+   +----------------------v--+
        |    Edge Node @ J1       |   |    Edge Node @ J2       |
        | RTSP -> YOLO -> Density |   | RTSP -> YOLO -> Density |
        | Webster optimizer       |   | Webster optimizer       |
        | Siren + GPS corridor    |   | Siren + GPS corridor    |
        +-------------+-----------+   +-------------+-----------+
                      |                             |
                 REST / Modbus                 REST / Modbus
                      |                             |
             +--------v--------+           +--------v--------+
             | Signal Hardware |           | Signal Hardware |
             +-----------------+           +-----------------+
```

## Folder layout

- `edge/`: edge runtime for RTSP, YOLO, signal plans, pre-emption, and MQTT
- `backend/`: FastAPI control plane with Redis and MQTT subscription
- `frontend/`: Vite React dashboard
- `simulation/`: zero-hardware traffic simulation
- `ml/`: YOLO and siren model training scripts
- `tests/`: pytest suite

## Quick start

1. `cd urbanmind`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r backend/requirements.txt -r edge/requirements.txt pytest rich`
4. `docker compose up -d redis mqtt`
5. `python3 simulation/run_sim.py --intersections 3 --duration 300 --inject-emergency 120`

One-command launcher:

```bash
chmod +x run_all.sh
./run_all.sh
```

Important:

- The pinned edge AI dependencies require Python `3.11`.
- If your default `python3` is newer, run:

```bash
PYTHON_BIN=$(command -v python3.11) ./run_all.sh
```

Optional:

- Backend: `cd backend && uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`

## Simulation command

```bash
python3 simulation/run_sim.py --intersections 3 --duration 300 --inject-emergency 120
```

The simulation runs three intersections in parallel, injects an emergency vehicle at simulation second 120, prints a live terminal table, and can optionally post state snapshots to the backend.

## Hardware setup guide for Jetson Nano

1. Flash JetPack and enable CUDA, camera, and audio drivers.
2. Install system packages for OpenCV, GStreamer RTSP support, and Python 3.11.
3. Clone this repo onto the Jetson and create a Python virtual environment.
4. Install `edge/requirements.txt` and copy `.env.example` to `.env`.
5. Set `RTSP_STREAM_URL`, `INTERSECTION_ID`, lane count, controller URL, and MQTT broker address.
6. Place trained weights at `models/yolov8n_indian.pt` and `models/siren_cnn.pt`.
7. Validate each module independently:
   `python3 edge/config.py`
   `python3 edge/detector.py`
   `python3 edge/siren_detector.py`
   `python3 edge/mqtt_client.py`
8. Run the edge pipeline under `systemd` or Docker with watchdog restart enabled.

## API reference

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Backend health status |
| `GET` | `/intersections` | Latest state for all intersections |
| `GET` | `/intersections/{id}` | Full state for a single intersection |
| `GET` | `/intersections/{id}/history?minutes=60` | Recent state history |
| `POST` | `/intersections/{id}/state` | Simulation/testing ingest endpoint |
| `POST` | `/signals/{id}/override` | Manual phase override |
| `DELETE` | `/signals/{id}/override` | Cancel manual override |
| `POST` | `/emergency/activate` | Activate emergency corridor |
| `POST` | `/emergency/update/{vehicle_id}` | Update vehicle GPS |
| `POST` | `/emergency/deactivate/{vehicle_id}` | Deactivate emergency corridor |
| `GET` | `/emergency/active` | List active corridors |
| `WS` | `/ws/live` | Live telemetry stream for dashboard |

## How to add a new intersection

1. Add the new intersection coordinates to `INTERSECTION_LOCATIONS_JSON`.
2. Add its default approach phase to `APPROACH_PHASE_MAP_JSON`.
3. Set edge `.env` values for `INTERSECTION_ID`, `RTSP_STREAM_URL`, and `LANE_COUNT`.
4. If the controller uses a unique endpoint, update `SIGNAL_CONTROLLER_URL`.
5. Start the edge runtime and confirm MQTT publishes to `urbanmind/intersection/{intersection_id}/state`.
6. Verify the backend shows the node in `/intersections` and the dashboard map.

## Notes

- `edge/detector.py` uses `yolov8n.pt` when the custom fine-tuned model is absent.
- `edge/signal_controller.py` supports `STUB_MODE=true` for development without hardware.
- `edge/siren_detector.py` disables itself cleanly when the model file is missing.
- `backend/services/redis_state.py` falls back to in-memory storage when Redis is unavailable.
