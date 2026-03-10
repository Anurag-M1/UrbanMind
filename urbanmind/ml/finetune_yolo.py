from __future__ import annotations

import shutil
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover - optional dependency
    YOLO = None


def finetune_yolo() -> None:
    """Fine-tunes YOLOv8 on the Indian traffic dataset.

    Args:
        None.

    Returns:
        None.
    """

    if YOLO is None:
        raise RuntimeError("ultralytics is not installed")
    project_root = Path(__file__).resolve().parent
    dataset_path = project_root / "datasets" / "indian_traffic" / "data.yaml"
    if not dataset_path.exists():
        raise FileNotFoundError(f"expected YOLO dataset config at {dataset_path}")
    output_dir = project_root / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO("yolov8n.pt")
    results = model.train(
        data=str(dataset_path),
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,
    )
    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    target_path = output_dir / "yolov8n_indian.pt"
    if best_weights.exists():
        shutil.copy2(best_weights, target_path)
    metrics = model.val(data=str(dataset_path))
    print(f"Validation mAP50: {metrics.box.map50:.4f}")


if __name__ == "__main__":
    finetune_yolo()
