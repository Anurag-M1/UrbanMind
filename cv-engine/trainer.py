"""
UrbanMind — YOLOv8 Fine-Tuning Script for Indian Roads
Fine-tunes YOLOv8n on Indian traffic datasets with additional classes
like auto-rickshaws, cattle, and cycle-rickshaws.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("urbanmind.trainer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)


def train(
    dataset_path: Optional[str] = None,
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    lr0: float = 0.01,
    model_name: str = "yolov8n.pt",
    output_dir: str = "models",
) -> None:
    """
    Fine-tune YOLOv8n on a custom Indian traffic dataset.

    Args:
        dataset_path: Path to dataset (Roboflow format) or None for demo.
        epochs: Number of training epochs.
        imgsz: Image size for training.
        batch: Batch size.
        lr0: Initial learning rate.
        model_name: Base model name to fine-tune from.
        output_dir: Directory to save fine-tuned weights.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        return

    logger.info("=" * 60)
    logger.info("UrbanMind YOLOv8 Fine-Tuning Script")
    logger.info("=" * 60)

    # Load base model
    model = YOLO(model_name)
    logger.info("Loaded base model: %s", model_name)

    if dataset_path is None:
        logger.warning("No dataset path provided — creating demo dataset config")
        dataset_path = _create_demo_dataset()
        if dataset_path is None:
            logger.error("Failed to create demo dataset — aborting training")
            return

    # Configure training
    logger.info("Training configuration:")
    logger.info("  Dataset: %s", dataset_path)
    logger.info("  Epochs: %d", epochs)
    logger.info("  Image size: %d", imgsz)
    logger.info("  Batch size: %d", batch)
    logger.info("  Learning rate: %f", lr0)

    # Run training
    results = model.train(
        data=dataset_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        lr0=lr0,
        augment=True,
        mosaic=1.0,
        flipud=0.5,
        fliplr=0.5,
        project=output_dir,
        name="yolov8n_india",
        exist_ok=True,
        verbose=True,
    )

    # Print validation metrics
    logger.info("=" * 60)
    logger.info("Training Complete!")
    if hasattr(results, "results_dict"):
        metrics = results.results_dict
        logger.info("Validation mAP@0.5: %.4f", metrics.get("metrics/mAP50(B)", 0))
        logger.info("Validation mAP@0.5:0.95: %.4f", metrics.get("metrics/mAP50-95(B)", 0))
    logger.info("=" * 60)

    # Save best weights
    best_weights = os.path.join(output_dir, "yolov8n_india", "weights", "best.pt")
    final_path = os.path.join(output_dir, "yolov8n_india.pt")
    if os.path.exists(best_weights):
        import shutil
        shutil.copy2(best_weights, final_path)
        logger.info("Best weights saved to: %s", final_path)

    # Export to TorchScript for edge deployment
    try:
        model_best = YOLO(final_path)
        model_best.export(format="torchscript")
        logger.info("TorchScript export saved to: %s", os.path.join(output_dir, "yolov8n_india.torchscript"))
    except Exception as exc:
        logger.warning("TorchScript export failed: %s", exc)


def _create_demo_dataset() -> Optional[str]:
    """Create a minimal demo dataset configuration for testing."""
    import yaml

    config = {
        "path": "demo_dataset",
        "train": "images/train",
        "val": "images/val",
        "names": {
            0: "person",
            1: "bicycle",
            2: "car",
            3: "motorcycle",
            4: "bus",
            5: "truck",
            6: "auto_rickshaw",
            7: "cattle",
            8: "cycle_rickshaw",
        },
        "nc": 9,
    }

    os.makedirs("demo_dataset/images/train", exist_ok=True)
    os.makedirs("demo_dataset/images/val", exist_ok=True)
    os.makedirs("demo_dataset/labels/train", exist_ok=True)
    os.makedirs("demo_dataset/labels/val", exist_ok=True)

    # Create minimal dummy images and labels
    import numpy as np
    for split in ["train", "val"]:
        for i in range(5):
            img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            cv2_path = f"demo_dataset/images/{split}/img_{i:03d}.jpg"
            try:
                import cv2
                cv2.imwrite(cv2_path, img)
            except Exception:
                pass

            label_path = f"demo_dataset/labels/{split}/img_{i:03d}.txt"
            with open(label_path, "w") as f:
                # Random bounding boxes
                for _ in range(3):
                    cls = np.random.randint(0, 9)
                    cx, cy = np.random.uniform(0.2, 0.8, 2)
                    w, h = np.random.uniform(0.05, 0.2, 2)
                    f.write(f"{cls} {cx:.4f} {cy:.4f} {w:.4f} {h:.4f}\n")

    config_path = "demo_dataset/data.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    logger.info("Demo dataset created at: demo_dataset/")
    return config_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UrbanMind YOLOv8 Fine-Tuning")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset path or Roboflow URL")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.01)
    args = parser.parse_args()

    train(
        dataset_path=args.dataset,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr0=args.lr,
    )
