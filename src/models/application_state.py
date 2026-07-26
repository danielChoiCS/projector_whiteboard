"""Aggregate application status model consumed by the GUI status section."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.system_state import SystemState


@dataclass(frozen=True)
class ApplicationState:
    """Overall status of the application at a single point in time.

    Attributes:
        system_state: Current high-level lifecycle state.
        camera_connected: Whether a camera feed is currently available.
        tracking_active: Whether hand tracking is currently producing data.
        calibrated: Whether a valid calibration transform is available.
        message: Human-readable status text for display in the GUI.
        error: Error description if ``system_state`` is ``SystemState.ERROR``,
            otherwise None.
    """

    system_state: SystemState
    camera_connected: bool
    tracking_active: bool
    calibrated: bool
    message: str
    error: str | None = None
