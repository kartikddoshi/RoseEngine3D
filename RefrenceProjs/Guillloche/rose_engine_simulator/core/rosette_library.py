"""rosette_library.py

Light-weight library holding standard and custom rosette wheel definitions used
in rose-engine simulation.  Each *rosette* is modelled as a simple harmonic
cam: the cutter offset is proportional to sin(m·θ + φ) where *m* = *tooth_count*.

This module does **not** handle the full compound kinematics (that belongs in a
higher-level motion planner) – it simply stores metadata and provides helper
methods for basic angular relationships.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import mpmath as mp # For consistency if needed, though numpy might be enough for profile interpolation
from scipy.interpolate import interp1d # For custom profiles

_DEFAULT_LIBRARY: Dict[str, int] = {
    "R12": 12,
    "R16": 16,
    "R20": 20,
    "R24": 24,
    "R30": 30,
    "R36": 36,
    "R48": 48,
    "R60": 60,
    "R72": 72,
    "R96": 96,
    "R120": 120,
}


@dataclass
class Rosette:
    name: str
    teeth: int
    eccentric_mm: float = 0.0  # positive -> off-centre amount
    profile_file: Optional[Path] = None  # optional custom radial profile (CSV)
    notes: str = ""
    _profile_data: Optional[Tuple[np.ndarray, np.ndarray]] = field(default=None, repr=False, init=False) # Cached profile data
    _interpolator: Optional[interp1d] = field(default=None, repr=False, init=False) # Cached interpolator

    # ------------------------------------------------------------------
    # Simple helpers
    # ------------------------------------------------------------------
    def _load_profile(self):
        """Loads and prepares the custom profile data if specified."""
        if self.profile_file and self.profile_file.exists():
            try:
                # CSV format: angle_rad, displacement_factor (0 to 2*pi, -1 to 1)
                data = np.loadtxt(self.profile_file, delimiter=',', skiprows=1) # Skip header row
                if data.shape[1] != 2:
                    print(f"Warning: Profile file {self.profile_file} has incorrect format. Expected 2 columns.")
                    self._profile_data = None
                    self._interpolator = None
                    return

                theta_profile = data[:, 0]
                displacement_profile = data[:, 1]

                # Ensure the profile covers a full 2*pi cycle for proper interpolation
                if not (np.isclose(theta_profile[0], 0.0) and np.isclose(theta_profile[-1], 2 * np.pi)):
                    print(f"Warning: Profile {self.profile_file} should span 0 to 2*pi. Adjusting endpoints.")
                    # This is a simple fix; more sophisticated handling might be needed
                    if not np.isclose(theta_profile[0], 0.0):
                        theta_profile = np.insert(theta_profile, 0, 0.0)
                        displacement_profile = np.insert(displacement_profile, 0, displacement_profile[0])
                    if not np.isclose(theta_profile[-1], 2 * np.pi):
                        theta_profile = np.append(theta_profile, 2*np.pi)
                        displacement_profile = np.append(displacement_profile, displacement_profile[-1])
                
                self._profile_data = (theta_profile, displacement_profile)
                # Use cubic interpolation for smoother profiles, ensure data is sorted by theta
                sorted_indices = np.argsort(theta_profile)
                self._interpolator = interp1d(theta_profile[sorted_indices], displacement_profile[sorted_indices], 
                                              kind='cubic', fill_value="extrapolate")
                print(f"Successfully loaded custom profile: {self.profile_file}")
            except Exception as e:
                print(f"Error loading profile file {self.profile_file}: {e}")
                self._profile_data = None
                self._interpolator = None
        else:
            self._profile_data = None
            self._interpolator = None

    def angular_to_radial(self, theta_rad: float) -> float:
        """Return *unit* radial displacement (range –1…+1) for given angle.
        Uses custom profile if available, otherwise defaults to sine wave.
        """
        if self._interpolator is None and self.profile_file:
            self._load_profile() # Attempt to load on first use

        # Normalize theta_rad to be within [0, 2*pi) for interpolation lookup
        normalized_theta = mp.fmod(mp.mpf(str(theta_rad)), 2 * mp.pi)
        if normalized_theta < 0:
            normalized_theta += 2 * mp.pi

        if self._interpolator:
            # Interpolator expects float, so convert mpf back if necessary
            # The precision of the profile itself dictates output precision here.
            return float(self._interpolator(float(normalized_theta)))
        else:
            # Default simple harmonic motion if no profile
            return float(mp.sin(self.teeth * mp.mpf(str(theta_rad)))) # Using mpf for calculation then float for consistency

    # For UI display
    def to_dict(self) -> Dict[str, str | int | float]:
        return {
            "name": self.name,
            "teeth": self.teeth,
            "eccentric_mm": self.eccentric_mm,
            "profile_file": str(self.profile_file) if self.profile_file else "",
            "notes": self.notes,
        }


class RosetteLibrary:
    """Keeps a registry of available rosettes.  Custom rosettes can be added /
    persisted to disk as simple JSON.
    """

    def __init__(self, storage: Path | None = None):
        self._storage = storage or Path(__file__).with_suffix(".json")
        self._items: Dict[str, Rosette] = {name: Rosette(name, teeth)
                                           for name, teeth in _DEFAULT_LIBRARY.items()}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._storage.exists():
            try:
                data = json.loads(self._storage.read_text())
                for entry in data:
                    self._items[entry["name"]] = Rosette(
                        name=entry["name"],
                        teeth=int(entry["teeth"]),
                        eccentric_mm=float(entry.get("eccentric_mm", 0.0)),
                        profile_file=Path(entry["profile_file"]) if entry.get("profile_file") else None,
                        notes=entry.get("notes", ""),
                    )
            except Exception as exc:
                print(f"[RosetteLibrary] Failed to load {self._storage}: {exc}")

    def _save(self) -> None:
        data: List[Dict[str, str | int | float]] = [r.to_dict() for r in self._items.values()]
        try:
            self._storage.write_text(json.dumps(data, indent=2))
        except Exception as exc:
            print(f"[RosetteLibrary] Failed to save {self._storage}: {exc}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_names(self) -> List[str]:
        return list(self._items.keys())

    def get(self, name: str) -> Rosette:
        if name not in self._items:
            raise KeyError(name)
        return self._items[name]

    def add(self, rosette: Rosette, *, persist: bool = True) -> None:
        self._items[rosette.name] = rosette
        if persist:
            self._save()

    def remove(self, name: str, *, persist: bool = True) -> None:
        self._items.pop(name, None)
        if persist:
            self._save()
