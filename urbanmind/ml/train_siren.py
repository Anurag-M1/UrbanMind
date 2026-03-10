from __future__ import annotations

import random
from pathlib import Path
from typing import Any

try:
    import librosa
except ImportError:  # pragma: no cover - optional dependency
    librosa = None

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset, random_split
except ImportError:  # pragma: no cover - optional dependency
    torch = None
    nn = None
    Dataset = object  # type: ignore[assignment]
    DataLoader = Any  # type: ignore[assignment]


if nn is not None:

    class SirenCNN(nn.Module):
        """CNN architecture for acoustic siren classification."""

        def __init__(self) -> None:
            """Initializes the CNN model.

            Args:
                None.

            Returns:
                None.
            """

            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d((1, 1)),
            )
            self.classifier = nn.Linear(128, 2)

        def forward(self, inputs: torch.Tensor) -> torch.Tensor:
            """Runs a forward pass.

            Args:
                inputs: Input batch tensor.

            Returns:
                Output logits.
            """

            features = self.features(inputs).flatten(1)
            return self.classifier(features)

else:

    class SirenCNN:  # type: ignore[no-redef]
        """Placeholder CNN when torch is unavailable."""

        def __init__(self) -> None:
            """Initializes the placeholder.

            Args:
                None.

            Returns:
                None.
            """

            return


class SirenDataset(Dataset):
    """Loads siren and ambient audio into mel-spectrogram tensors."""

    def __init__(self, root: Path) -> None:
        """Initializes the dataset.

        Args:
            root: Dataset root directory.

        Returns:
            None.
        """

        self.samples: list[tuple[Path, int]] = []
        for label, folder in enumerate(["negative", "positive"]):
            for audio_file in sorted((root / folder).glob("*.wav")):
                self.samples.append((audio_file, label))
        random.shuffle(self.samples)

    def __len__(self) -> int:
        """Returns dataset length.

        Args:
            None.

        Returns:
            Number of samples.
        """

        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[Any, int]:
        """Loads one sample.

        Args:
            index: Sample index.

        Returns:
            Tuple of tensor and label.
        """

        if librosa is None or np is None or torch is None:
            raise RuntimeError("training dependencies are not installed")
        path, label = self.samples[index]
        audio, _ = librosa.load(path, sr=22050, mono=True, duration=1.0)
        mel = librosa.feature.melspectrogram(y=audio, sr=22050, n_mels=128, hop_length=512)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        mel_db = mel_db[:, :87]
        if mel_db.shape[1] < 87:
            mel_db = np.pad(mel_db, ((0, 0), (0, 87 - mel_db.shape[1])))
        tensor = torch.tensor(mel_db, dtype=torch.float32).unsqueeze(0)
        return tensor, label


def _evaluate(model: Any, loader: Any, device: Any) -> float:
    """Evaluates classification accuracy.

    Args:
        model: Model to evaluate.
        loader: Validation loader.
        device: Torch device.

    Returns:
        Accuracy score.
    """

    if torch is None:
        return 0.0
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            predictions = model(inputs).argmax(dim=1)
            correct += int((predictions == labels).sum().item())
            total += int(labels.numel())
    return correct / max(1, total)


def train_siren() -> None:
    """Trains the siren classifier with early stopping.

    Args:
        None.

    Returns:
        None.
    """

    if torch is None or librosa is None or np is None:
        raise RuntimeError("training dependencies are not installed")
    root = Path(__file__).resolve().parent
    dataset_root = root / "datasets" / "siren"
    model_output = root / "models"
    model_output.mkdir(parents=True, exist_ok=True)
    dataset = SirenDataset(dataset_root)
    train_size = int(len(dataset) * 0.8)
    val_size = len(dataset) - train_size
    train_set, val_set = random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=32)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SirenCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    best_accuracy = 0.0
    patience = 5
    patience_left = patience
    for epoch in range(30):
        model.train()
        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(inputs), labels)
            loss.backward()
            optimizer.step()
        accuracy = _evaluate(model, val_loader, device)
        print(f"epoch={epoch + 1} val_accuracy={accuracy:.4f}")
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            patience_left = patience
            torch.save(model.state_dict(), model_output / "siren_cnn.pt")
        else:
            patience_left -= 1
            if patience_left == 0:
                break
    print(f"Best validation accuracy: {best_accuracy:.4f}")


if __name__ == "__main__":
    train_siren()
