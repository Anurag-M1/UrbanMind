"""
UrbanMind — Edge Inference Benchmark
Measures FPS, latency percentiles, and memory usage for YOLOv8 inference.
Reports whether Jetson Nano 15 FPS target is met.
"""

import logging
import os
import time
from typing import Dict

import numpy as np

logger = logging.getLogger("urbanmind.benchmark")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")


def run_benchmark(
    model_path: str = "models/yolov8n.pt",
    num_frames: int = 100,
    imgsz: int = 640,
) -> Dict[str, object]:
    """
    Run inference benchmark on the given model.

    Measures:
        - Average FPS
        - P50, P95, P99 latency in milliseconds
        - Peak memory usage in MB

    Args:
        model_path: Path to YOLOv8 model weights.
        num_frames: Number of test frames to process.
        imgsz: Input image size.

    Returns:
        Dictionary with all benchmark results.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        return {"error": "ultralytics not available"}

    import torch

    logger.info("=" * 60)
    logger.info("UrbanMind Edge Inference Benchmark")
    logger.info("=" * 60)
    logger.info("Model: %s", model_path)
    logger.info("Frames: %d", num_frames)
    logger.info("Image size: %d", imgsz)

    # Detect device
    device_gpu = "cuda" if torch.cuda.is_available() else None
    device_cpu = "cpu"

    results = {}

    for device_name, device in [("GPU", device_gpu), ("CPU", device_cpu)]:
        if device is None:
            logger.info("Skipping %s benchmark — not available", device_name)
            continue

        logger.info("\n--- %s Benchmark ---", device_name)

        # Load model
        model = YOLO(model_path)

        # Generate random test frames
        test_frames = [
            np.random.randint(0, 255, (imgsz, imgsz, 3), dtype=np.uint8)
            for _ in range(num_frames)
        ]

        # Warmup
        logger.info("Warming up (5 frames)...")
        for i in range(5):
            model(test_frames[0], device=device, verbose=False)

        # Benchmark
        latencies = []
        logger.info("Running benchmark (%d frames)...", num_frames)

        for frame in test_frames:
            start = time.perf_counter()
            model(frame, device=device, verbose=False)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            latencies.append(elapsed)

        # Calculate metrics
        latencies = np.array(latencies)
        avg_fps = 1000.0 / np.mean(latencies)
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        # Memory usage
        try:
            import psutil
        except ImportError:
            process = None
            memory_mb = 0.0
        else:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / (1024 * 1024)

        # Check Jetson Nano target
        meets_target = avg_fps >= 15.0

        device_results = {
            "device": device_name,
            "avg_fps": round(avg_fps, 1),
            "p50_latency_ms": round(p50, 1),
            "p95_latency_ms": round(p95, 1),
            "p99_latency_ms": round(p99, 1),
            "min_latency_ms": round(float(np.min(latencies)), 1),
            "max_latency_ms": round(float(np.max(latencies)), 1),
            "memory_mb": round(memory_mb, 1),
            "meets_jetson_target": meets_target,
        }
        results[device_name] = device_results

        logger.info("  Avg FPS:       %.1f", avg_fps)
        logger.info("  P50 latency:   %.1f ms", p50)
        logger.info("  P95 latency:   %.1f ms", p95)
        logger.info("  P99 latency:   %.1f ms", p99)
        logger.info("  Memory:        %.1f MB", memory_mb)
        logger.info("  Jetson target: %s", "✓ MET" if meets_target else "✗ NOT MET")

    # Print summary table
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 60)
    logger.info("%-8s %-10s %-12s %-12s %-12s %-10s %-10s", "Device", "Avg FPS", "P50 (ms)", "P95 (ms)", "P99 (ms)", "Memory", "Target")
    logger.info("-" * 74)
    for device_name, dr in results.items():
        target_str = "✓" if dr["meets_jetson_target"] else "✗"
        logger.info(
            "%-8s %-10.1f %-12.1f %-12.1f %-12.1f %-10.1f %-10s",
            dr["device"], dr["avg_fps"], dr["p50_latency_ms"],
            dr["p95_latency_ms"], dr["p99_latency_ms"], dr["memory_mb"], target_str,
        )

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UrbanMind Inference Benchmark")
    parser.add_argument("--model", default="models/yolov8n.pt", help="Model path")
    parser.add_argument("--frames", type=int, default=100, help="Number of test frames")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    args = parser.parse_args()

    run_benchmark(args.model, args.frames, args.imgsz)
