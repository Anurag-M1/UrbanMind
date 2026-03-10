from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import EdgeConfig, configure_logging, load_config
from edge.optimizer import Phase, SignalPlan


LOGGER = configure_logging(__name__)


@dataclass(slots=True)
class PhaseStatus:
    """Stores the current controller phase status."""

    direction: str
    remaining_seconds: int
    source: str


class SignalControllerClient:
    """Applies plans to physical or simulated signal controllers."""

    def __init__(self, config: EdgeConfig) -> None:
        """Initializes the signal controller client.

        Args:
            config: Edge runtime configuration.

        Returns:
            None.
        """

        self.config = config

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Sends a JSON request to the signal controller.

        Args:
            method: HTTP method name.
            path: Endpoint path.
            payload: Optional JSON payload.

        Returns:
            Parsed response dictionary.
        """

        url = f"{self.config.signal_controller_url.rstrip('/')}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8") or "{}"
            return json.loads(body)

    def apply_plan(self, signal_plan: SignalPlan) -> bool:
        """Applies a signal plan to the controller.

        Args:
            signal_plan: Plan to push.

        Returns:
            True when the controller accepted the plan.
        """

        if self.config.stub_mode:
            print(f"[STUB] apply_plan {signal_plan.to_dict()}")
            return True
        try:
            self._request("POST", "/plans/apply", signal_plan.to_dict())
            return True
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            LOGGER.critical("failed to apply signal plan: %s", exc)
            self.revert_to_fixed_timer()
            return False

    def get_current_phase(self) -> PhaseStatus:
        """Fetches the currently active controller phase.

        Args:
            None.

        Returns:
            Phase status from the controller.
        """

        if self.config.stub_mode:
            return PhaseStatus(direction="north-south", remaining_seconds=25, source="stub")
        try:
            payload = self._request("GET", "/phase")
            return PhaseStatus(
                direction=str(payload.get("direction", "unknown")),
                remaining_seconds=int(payload.get("remaining_seconds", 0)),
                source="controller",
            )
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            LOGGER.critical("failed to read current phase: %s", exc)
            self.revert_to_fixed_timer()
            return PhaseStatus(direction="fixed-timer", remaining_seconds=0, source="failsafe")

    def emergency_override(self, phase_direction: str, duration_seconds: int) -> bool:
        """Applies a temporary emergency override.

        Args:
            phase_direction: Phase to hold green.
            duration_seconds: Override duration.

        Returns:
            True when the override was accepted.
        """

        if self.config.stub_mode:
            print(f"[STUB] emergency_override phase={phase_direction} duration={duration_seconds}")
            return True
        try:
            self._request(
                "POST",
                "/emergency/override",
                {"phase_direction": phase_direction, "duration_seconds": duration_seconds},
            )
            return True
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            LOGGER.critical("failed to push emergency override: %s", exc)
            self.revert_to_fixed_timer()
            return False

    def revert_to_fixed_timer(self) -> bool:
        """Returns the controller to a fixed-timer plan.

        Args:
            None.

        Returns:
            True when the revert command succeeded or stubbed.
        """

        if self.config.stub_mode:
            print("[STUB] revert_to_fixed_timer")
            return True
        try:
            self._request("POST", "/revert")
            return True
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            LOGGER.critical("failed to revert signal controller: %s", exc)
            return False


def main() -> None:
    """Runs a signal controller smoke test.

    Args:
        None.

    Returns:
        None.
    """

    client = SignalControllerClient(load_config())
    plan = SignalPlan(cycle_length=60, phases=[Phase(direction="north-south", green_duration=28), Phase(direction="east-west", green_duration=24)])
    LOGGER.info("apply_plan=%s", client.apply_plan(plan))
    LOGGER.info("current_phase=%s", asdict(client.get_current_phase()))


if __name__ == "__main__":
    main()
