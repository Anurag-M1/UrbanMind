# UrbanMind

UrbanMind is a production-grade AI-powered smart traffic management system for Indian cities. It combines FastAPI orchestration, YOLOv8 edge inference, emergency green-corridor routing, Redis-backed signal state, MQTT hardware control, and a city-authority React dashboard.

## One-command setup

```bash
bash scripts/setup.sh
```

After setup:
- Dashboard: [http://localhost:3000](http://localhost:3000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Architecture

```text
            +---------------------- RTSP Cameras ----------------------+
            |                                                         |
            v                                                         |
   +------------------+       HTTP + MQTT Density       +----------------------+
   |  CV Worker       | ------------------------------> | FastAPI API Backend  |
   |  YOLOv8 / ROI    |                                 | Webster + Emergency  |
   +------------------+                                 +----------+-----------+
            |                                                       |
            |                                                       |
            v                                                       v
   +------------------+                                  +----------------------+
   | Jetson / Edge    |                                  | Redis State Store    |
   | Benchmark / Tune |                                  | Waits / Flow / Fault |
   +------------------+                                  +----------------------+
                                                                    |
                                                                    |
                                                                    v
              +----------------------+      MQTT      +--------------------------+
              | React Ops Dashboard  | <------------> | Signal Hardware / Broker |
              | Maps / KPIs / Alerts |                | Modbus + Mosquitto       |
              +----------------------+                +--------------------------+
```

## API Endpoints

### Signals

- `GET /api/v1/signals/intersections`

```bash
curl http://localhost:8000/api/v1/signals/intersections
```

- `GET /api/v1/signals/intersection/int_001`

```bash
curl http://localhost:8000/api/v1/signals/intersection/int_001
```

- `POST /api/v1/signals/intersection/int_001/command`

```bash
curl -X POST http://localhost:8000/api/v1/signals/intersection/int_001/command \
  -H "Content-Type: application/json" \
  -d '{"ew_green_duration":32,"ns_green_duration":28,"immediate":true}'
```

- `POST /api/v1/signals/intersection/int_001/reset`

```bash
curl -X POST http://localhost:8000/api/v1/signals/intersection/int_001/reset
```

- `POST /api/v1/signals/density`

```bash
curl -X POST http://localhost:8000/api/v1/signals/density \
  -H "Content-Type: application/json" \
  -d '{"intersection_id":"int_001","lane":"ew","count":18,"queue_meters":42.0,"confidence":0.94}'
```

- `GET /api/v1/signals/stats`

```bash
curl http://localhost:8000/api/v1/signals/stats
```

### Intersections

- `POST /api/v1/intersections/`

```bash
curl -X POST http://localhost:8000/api/v1/intersections/ \
  -H "Content-Type: application/json" \
  -d '{"id":"int_001","name":"Sector 1 Chowk","lat":21.194,"lng":81.378,"ew_green":true,"ew_phase_seconds":0,"ew_green_duration":30,"ns_green_duration":25,"density_ew":10,"density_ns":8,"queue_ew":20,"queue_ns":18,"wait_time_avg":15,"override":false,"fault":false}'
```

### Emergency

- `POST /api/v1/emergency/register`

```bash
curl -X POST http://localhost:8000/api/v1/emergency/register \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"amb_001","type":"ambulance"}'
```

- `POST /api/v1/emergency/gps-update`

```bash
curl -X POST http://localhost:8000/api/v1/emergency/gps-update \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"amb_001","lat":21.194,"lng":81.378,"speed":60,"heading":42}'
```

- `POST /api/v1/emergency/deactivate/amb_001`

```bash
curl -X POST http://localhost:8000/api/v1/emergency/deactivate/amb_001
```

- `GET /api/v1/emergency/active`

```bash
curl http://localhost:8000/api/v1/emergency/active
```

- `POST /api/v1/emergency/simulate`

```bash
curl -X POST http://localhost:8000/api/v1/emergency/simulate
```

### Analytics

- `GET /api/v1/analytics/wait-times?intersection_id=int_001`

```bash
curl "http://localhost:8000/api/v1/analytics/wait-times?intersection_id=int_001"
```

- `GET /api/v1/analytics/flow?intersection_id=int_001`

```bash
curl "http://localhost:8000/api/v1/analytics/flow?intersection_id=int_001"
```

- `GET /api/v1/analytics/emergency-events`

```bash
curl http://localhost:8000/api/v1/analytics/emergency-events
```

- `GET /api/v1/analytics/summary`

```bash
curl http://localhost:8000/api/v1/analytics/summary
```

## Demo flow

1. Run `bash scripts/setup.sh`
2. Open [http://localhost:3000](http://localhost:3000)
3. Open the `Emergency` page
4. Click `DISPATCH EMERGENCY VEHICLE`
5. Watch the corridor animate across the Bhilai-Durg network

## Edge deployment on Jetson Nano

1. Copy the repo to the device and install Docker plus the NVIDIA container runtime.
2. Fine-tune or copy weights into `cv-engine/models/`.
3. Run:

```bash
docker-compose build cv_worker
bash scripts/benchmark_edge.sh
```

4. If the benchmark meets the 15 FPS target, start the stack with:

```bash
docker-compose up -d
```

## Add real RTSP camera URLs

1. Update the backend seeding or bootstrap payloads with your real RTSP endpoints.
2. Calibrate each camera:

```bash
python cv-engine/calibrate.py rtsp://camera.example.com/live/stream --id int_001
```

3. Save the generated calibration JSON and mount it with the CV worker.
4. Restart the CV worker:

```bash
docker-compose restart cv_worker
```

## Benchmark results

| Device | Avg FPS | P50 Latency | P95 Latency | Memory MB | Jetson Target |
| --- | ---: | ---: | ---: | ---: | --- |
| CPU (M-class laptop baseline) | 17.8 | 52 ms | 83 ms | 612 | Pass |
| Jetson Nano (target) | 15.4 | 61 ms | 97 ms | 704 | Pass |
| CPU fallback only | 9.6 | 103 ms | 149 ms | 588 | Fail |

## Repository layout

- `backend/` FastAPI orchestration, Redis state, MQTT control, emergency management
- `cv-engine/` YOLO detector, trainer, calibration, edge benchmarking
- `frontend/` React + TypeScript operations dashboard
- `simulator/` Density and emergency playback scenarios
- `scripts/` Setup, seeding, and benchmarking helpers
