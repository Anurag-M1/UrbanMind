from __future__ import annotations

import argparse
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover - optional dependency
    YOLO = None


def evaluate_yolo(model_path: Path, dataset_path: Path) -> None:
    """Runs YOLO validation and prints accuracy metrics.

    Args:
        model_path: Path to trained YOLO weights.
        dataset_path: Path to data.yaml.

    Returns:
        None.
    """

    if YOLO is None:
        raise RuntimeError("ultralytics is not installed")
    model = YOLO(str(model_path))
    metrics = model.val(data=str(dataset_path))
    print(f"mAP50={metrics.box.map50:.4f} mAP50-95={metrics.box.map:.4f}")


def main() -> None:
    """Parses CLI arguments and runs evaluation.

    Args:
        None.

    Returns:
        None.
    """

    parser = argparse.ArgumentParser(description="Evaluate UrbanMind ML models")
    parser.add_argument("--model", type=Path, default=Path("models/yolov8n_indian.pt"))
    parser.add_argument("--dataset", type=Path, default=Path("datasets/indian_traffic/data.yaml"))
    args = parser.parse_args()
    evaluate_yolo(Path(__file__).resolve().parent / args.model, Path(__file__).resolve().parent / args.dataset)


if __name__ == "__main__":
    main()
