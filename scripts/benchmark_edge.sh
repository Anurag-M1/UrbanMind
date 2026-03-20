#!/bin/bash
# UrbanMind Jetson Nano benchmark helper.

set -e

echo "UrbanMind Edge Benchmark"
docker-compose build cv_worker
docker-compose run --rm cv_worker python benchmark.py --model models/yolov8n.pt --frames 100 --imgsz 640
