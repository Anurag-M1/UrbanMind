from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import EdgeConfig, configure_logging, load_config

try:
    import librosa
except ImportError:  # pragma: no cover - optional dependency
    librosa = None

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency
    sd = None

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - optional dependency
    torch = None
    nn = None


LOGGER = configure_logging(__name__)


@dataclass(slots=True)
class SirenEvent:
    """Stores the outcome of siren inference."""

    detected: bool
    confidence: float
    timestamp: str


if nn is not None:

    class SirenCNN(nn.Module):
        """Simple three-layer CNN for siren classification."""

        def __init__(self) -> None:
            """Initializes the CNN architecture.

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
                inputs: Input mel-spectrogram batch.

            Returns:
                Class logits.
            """

            features = self.features(inputs).flatten(1)
            return self.classifier(features)

else:

    class SirenCNN:  # type: ignore[no-redef]
        """Placeholder CNN used when torch is unavailable."""

        def __init__(self) -> None:
            """Initializes the placeholder model.

            Args:
                None.

            Returns:
                None.
            """


class AcousticSirenDetector:
    """Reads microphone audio and classifies siren events."""

    def __init__(self, config: EdgeConfig, threshold: float = 0.85) -> None:
        """Initializes the siren detector.

        Args:
            config: Edge runtime configuration.
            threshold: Positive siren confidence threshold.

        Returns:
            None.
        """

        self.config = config
        self.threshold = threshold
        self.enabled = False
        self.model = self._load_model()

    def _load_model(self) -> Any:
        """Loads a pretrained model when available.

        Args:
            None.

        Returns:
            Loaded model object or None.
        """

        model_path = Path(self.config.siren_model_path)
        if torch is None or librosa is None or np is None or sd is None:
            LOGGER.warning("siren dependencies missing; acoustic detection disabled")
            return None
        if not model_path.exists():
            LOGGER.warning("no siren model file found at %s; acoustic detection disabled", model_path)
            return None
        model = SirenCNN()
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()
        self.enabled = True
        return model

    def _record_chunk(self, seconds: int = 1) -> Any:
        """Records one chunk of audio from the default microphone.

        Args:
            seconds: Recording duration in seconds.

        Returns:
            Raw waveform array.
        """

        if not self.enabled or sd is None:
            return None
        samples = int(22050 * seconds)
        audio = sd.rec(samples, samplerate=22050, channels=1, dtype="float32")
        sd.wait()
        return audio.squeeze()

    def _preprocess(self, audio: Any) -> Any:
        """Converts waveform audio to a fixed-size mel-spectrogram tensor.

        Args:
            audio: Raw waveform array.

        Returns:
            Model-ready tensor or None.
        """

        if not self.enabled or librosa is None or np is None or torch is None:
            return None
        mel = librosa.feature.melspectrogram(
            y=audio,
            sr=22050,
            n_mels=128,
            hop_length=512,
        )
        mel_db = librosa.power_to_db(mel, ref=np.max)
        mel_db = mel_db[:, :87]
        if mel_db.shape[1] < 87:
            pad_width = 87 - mel_db.shape[1]
            mel_db = np.pad(mel_db, ((0, 0), (0, pad_width)))
        tensor = torch.tensor(mel_db, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        return tensor

    def listen_once(self) -> SirenEvent:
        """Records one second of audio and returns the classification result.

        Args:
            None.

        Returns:
            Siren event classification.
        """

        if not self.enabled or self.model is None or torch is None:
            return SirenEvent(
                detected=False,
                confidence=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        audio = self._record_chunk()
        tensor = self._preprocess(audio)
        if tensor is None:
            return SirenEvent(
                detected=False,
                confidence=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = torch.softmax(logits, dim=1).squeeze(0)
            confidence = float(probabilities[1].item())
        return SirenEvent(
            detected=confidence >= self.threshold,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def main() -> None:
    """Runs a one-shot siren detection smoke test.

    Args:
        None.

    Returns:
        None.
    """

    detector = AcousticSirenDetector(load_config())
    LOGGER.info("siren_event=%s", detector.listen_once())


if __name__ == "__main__":
    main()
