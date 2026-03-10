# Datasets

## Indian traffic detector dataset

Place the YOLO-format traffic dataset at:

`datasets/indian_traffic/`

Expected files:

- `data.yaml`
- `train/images`, `train/labels`
- `val/images`, `val/labels`

Recommended sources:

- AI City style road-scene datasets adapted to local classes
- Open municipal CCTV captures labeled in YOLO format
- Indian mixed-traffic datasets including buses, trucks, motorcycles, auto-rickshaws, and pedestrians

## Siren classifier dataset

Place audio data at:

- `datasets/siren/positive/*.wav` for siren clips
- `datasets/siren/negative/*.wav` for urban ambient audio

Use 1-second mono WAV clips. Normalize labels carefully to avoid leakage between train and validation sets.
