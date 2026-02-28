"""pattern_generator.py

Core module providing an extensible, high-precision pattern-generation engine.
Each pattern is represented as a subclass of `PatternGenerator`.

Why a new module?
-----------------
`core/math_model.py` already houses a sizable collection of pattern functions but
it has grown unwieldy and is difficult to compose/extend.  This module
abstracts pattern behaviour behind a class interface, making it trivial to
combine and nest patterns (e.g.
``SimpleRosette + 0.2 * BasketWeave``) and to introduce adaptive sampling or
other cross-cutting functionality.

Numerical backend
-----------------
We continue to use ``mpmath`` for micro-scale accuracy (≥ 1 µm) but defer to
``numpy`` for vectorised workflows.  All public methods accept either scalar
``float``/``mp.mpf`` or ``numpy.ndarray`` – every element is internally
converted to ``mp.mpf`` before evaluation.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence, Tuple, Union, overload

import mpmath as mp
import numpy as np

# High precision for watch-grade guilloche
mp.mp.dps = 50  # 50 decimal digits
Numeric = Union[float, int, mp.mpf]
ArrayLike = Union[np.ndarray, Sequence[Numeric]]


def _to_mpf(x: Numeric) -> mp.mpf:  # small helper
    """Convert a scalar to ``mp.mpf`` safely."""
    if isinstance(x, mp.mpf):
        return x
    return mp.mpf(str(x))


class PatternGenerator(ABC):
    """Abstract base class for all pattern generators."""

    def __init__(self, params: Dict[str, Any] | None = None) -> None:
        self.params = params or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @abstractmethod
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        """Return radial displacement for *theta* (radians)."""

    def sample(self, n_points: int = 1000, *, full_rotation: bool = True,
               start_angle: float = 0.0, end_angle: float | None = None) -> Tuple[np.ndarray, np.ndarray]:
        """Convenience wrapper returning *(θ, r)* arrays suitable for polar plotting."""
        if full_rotation:
            theta = np.linspace(0.0, 2 * np.pi, n_points)
        else:
            if end_angle is None:
                raise ValueError("end_angle must be provided when full_rotation=False")
            theta = np.linspace(start_angle, end_angle, n_points)
        return theta, self.radial(theta)

    # ------------------------------------------------------------------
    # Composition helpers
    # ------------------------------------------------------------------
    def __add__(self, other: "PatternGenerator") -> "CompoundPattern":
        return CompoundPattern([self, other])

    def __mul__(self, scalar: Numeric) -> "ScaledPattern":
        return ScaledPattern(self, scalar)

    __rmul__ = __mul__


# ----------------------------------------------------------------------
# Concrete pattern classes
# ----------------------------------------------------------------------

class SimpleRosette(PatternGenerator):
    """Standard rose-engine cam pattern  *R = A·sin(nθ + φ)*."""

    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        A = _to_mpf(self.params.get("amplitude", 0.5))
        n = _to_mpf(self.params.get("lobes", 6))
        phi = _to_mpf(self.params.get("phase", 0.0))
        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, t in enumerate(theta):
                out[i] = A * mp.sin(n * _to_mpf(t) + phi)
            return out
        return A * mp.sin(n * _to_mpf(theta) + phi)


class CustomHarmonic(PatternGenerator):
    """Sum of arbitrary harmonic components provided as a list of dicts.

    Example params::
        {
          "harmonics": [
              {"A": 0.3, "n": 7, "phi": 0},
              {"A": 0.1, "n": 14, "phi": 1.57}
          ]
        }
    """

    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        harmonics = self.params.get("harmonics", [])
        if isinstance(theta, np.ndarray):
            out = np.zeros(len(theta), dtype=object)
            for comp in harmonics:
                A = _to_mpf(comp.get("A", 0))
                n = _to_mpf(comp.get("n", 1))
                phi = _to_mpf(comp.get("phi", 0))
                for i, t in enumerate(theta):
                    out[i] += A * mp.sin(n * _to_mpf(t) + phi)
            return out
        t_mpf = _to_mpf(theta)
        total = mp.mpf(0)
        for comp in harmonics:
            A = _to_mpf(comp.get("A", 0))
            n = _to_mpf(comp.get("n", 1))
            phi = _to_mpf(comp.get("phi", 0))
            total += A * mp.sin(n * t_mpf + phi)
        return total


class Epitrochoid(PatternGenerator):
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        R = _to_mpf(self.params.get("R", 5))
        r = _to_mpf(self.params.get("r", 1))
        d = _to_mpf(self.params.get("d", 0.8))
        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, t in enumerate(theta):
                t_mpf = _to_mpf(t)
                x = (R + r) * mp.cos(t_mpf) - d * mp.cos(((R + r) / r) * t_mpf)
                y = (R + r) * mp.sin(t_mpf) - d * mp.sin(((R + r) / r) * t_mpf)
                out[i] = mp.sqrt(x ** 2 + y ** 2)
            return out
        t_mpf = _to_mpf(theta)
        x = (R + r) * mp.cos(t_mpf) - d * mp.cos(((R + r) / r) * t_mpf)
        y = (R + r) * mp.sin(t_mpf) - d * mp.sin(((R + r) / r) * t_mpf)
        return mp.sqrt(x ** 2 + y ** 2)


class Hypotrochoid(PatternGenerator):
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        R = _to_mpf(self.params.get("R", 5))
        r = _to_mpf(self.params.get("r", 3))
        d = _to_mpf(self.params.get("d", 1.2))
        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, t in enumerate(theta):
                t_mpf = _to_mpf(t)
                x = (R - r) * mp.cos(t_mpf) + d * mp.cos(((R - r) / r) * t_mpf)
                y = (R - r) * mp.sin(t_mpf) - d * mp.sin(((R - r) / r) * t_mpf)
                out[i] = mp.sqrt(x ** 2 + y ** 2)
            return out
        t_mpf = _to_mpf(theta)
        x = (R - r) * mp.cos(t_mpf) + d * mp.cos(((R - r) / r) * t_mpf)
        y = (R - r) * mp.sin(t_mpf) - d * mp.sin(((R - r) / r) * t_mpf)
        return mp.sqrt(x ** 2 + y ** 2)


class BasketWeave(PatternGenerator):
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        A = _to_mpf(self.params.get("amplitude", 0.4))
        n1 = _to_mpf(self.params.get("n1", 4))
        n2 = _to_mpf(self.params.get("n2", 8))
        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, t in enumerate(theta):
                t_mpf = _to_mpf(t)
                out[i] = A * (mp.sin(n1 * t_mpf) * mp.cos(n2 * t_mpf))
            return out
        t_mpf = _to_mpf(theta)
        return A * (mp.sin(n1 * t_mpf) * mp.cos(n2 * t_mpf))


class MoirePattern(PatternGenerator):
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        A = _to_mpf(self.params.get("amplitude", 0.4))
        n1 = _to_mpf(self.params.get("n1", 20))
        n2 = _to_mpf(self.params.get("n2", 21))
        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, t in enumerate(theta):
                t_mpf = _to_mpf(t)
                out[i] = A * mp.sin(n1 * t_mpf) * mp.sin(n2 * t_mpf)
            return out
        t_mpf = _to_mpf(theta)
        return A * mp.sin(n1 * t_mpf) * mp.sin(n2 * t_mpf)


class SunburstPattern(PatternGenerator):
    """Sunburst pattern with modulated rays.

    R = A * (1 - mod + mod * cos(n_rays * theta)^power)
    """
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        A = _to_mpf(self.params.get("amplitude", 0.5))
        n_rays = _to_mpf(self.params.get("rays", 24))
        modulation = _to_mpf(self.params.get("ray_modulation", 0.2))
        # Power term to sharpen or soften the ray peaks, higher power = sharper
        power = _to_mpf(self.params.get("ray_sharpness_power", 10))

        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, t in enumerate(theta):
                t_mpf = _to_mpf(t)
                cos_term = mp.cos(n_rays * t_mpf)
                # Ensure base for power is non-negative if power is not an integer
                # For positive integer powers, mpmath handles negative bases correctly.
                # However, for visual patterns, cos_term is usually expected to be positive or its magnitude taken.
                # Here, (cos_term)^power can lead to complex numbers if cos_term is negative and power is fractional.
                # Assuming power is an integer for typical sunburst sharpness.
                powered_cos_term = cos_term ** power
                out[i] = A * (mp.mpf('1') - modulation + modulation * powered_cos_term)
            return out
        
        t_mpf = _to_mpf(theta)
        cos_term = mp.cos(n_rays * t_mpf)
        powered_cos_term = cos_term ** power
        return A * (mp.mpf('1') - modulation + modulation * powered_cos_term)


class LinearGuilloche(PatternGenerator):
    """Generates a linear wave pattern, typically Y displacement as a function of X.
    For consistency, 'theta' is used as the input variable, representing linear progression.
    Y = A * sin(k*x + phi)
    """
    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        # 'radial' here means displacement perpendicular to the main progression axis
        A = _to_mpf(self.params.get("amplitude", 0.2))
        # 'wavelength' or 'frequency' (k = 2*pi/wavelength)
        k = _to_mpf(self.params.get("spatial_frequency_k", 1.0)) 
        phi = _to_mpf(self.params.get("phase", 0.0))

        if isinstance(theta, np.ndarray):
            out = np.empty_like(theta, dtype=object)
            for i, x_val in enumerate(theta):
                x_mpf = _to_mpf(x_val)
                out[i] = A * mp.sin(k * x_mpf + phi)
            return out
        
        x_mpf = _to_mpf(theta)
        return A * mp.sin(k * x_mpf + phi)


class SpiralPattern(PatternGenerator):
    """Archimedean spiral *r = a + bθ* with optional sine modulation."""

    def radial(self, theta: Union[ArrayLike, Numeric]) -> Union[np.ndarray, mp.mpf]:
        a = _to_mpf(self.params.get("a", 0.0))
        b = _to_mpf(self.params.get("b", 0.1))
        mod_amp = _to_mpf(self.params.get("mod_amp", 0))
        mod_freq = _to_mpf(self.params.get("mod_freq", 0))

        def _eval(t: Numeric) -> mp.mpf:
            r_val = a + b * _to_mpf(t)
            if mod_amp != 0:
                r_val += mod_amp * mp.sin(mod_freq * _to_mpf(t))
            return r_val

        if isinstance(theta, np.ndarray):
            return np.array([_eval(t) for t in theta], dtype=object)
        return _eval(theta)


# ----------------------------------------------------------------------
# Combinators / decorators
# ----------------------------------------------------------------------

class ScaledPattern(PatternGenerator):
    def __init__(self, base: PatternGenerator, scalar: Numeric) -> None:
        super().__init__()
        self.base = base
        self.scalar = _to_mpf(scalar)

    def radial(self, theta):  # type: ignore[override]
        r = self.base.radial(theta)
        if isinstance(r, np.ndarray):
            return self.scalar * r
        return self.scalar * r


class CompoundPattern(PatternGenerator):
    """Sum of multiple generators."""

    def __init__(self, parts: List[PatternGenerator]):
        super().__init__()
        self.parts = parts

    def radial(self, theta):  # type: ignore[override]
        accum: Union[np.ndarray, mp.mpf]
        first = self.parts[0].radial(theta)
        if isinstance(first, np.ndarray):
            accum = np.array(first, dtype=object)
        else:
            accum = first
        for p in self.parts[1:]:
            r = p.radial(theta)
            if isinstance(accum, np.ndarray):
                accum += r  # type: ignore[operator]
            else:
                accum = accum + r  # type: ignore[assignment]
        return accum


# ----------------------------------------------------------------------
# Factory helper
# ----------------------------------------------------------------------

PATTERN_MAP = {
    "standard": SimpleRosette,
    "simple_sine": SimpleRosette,
    "custom_harmonic": CustomHarmonic,
    "epitrochoid": Epitrochoid,
    "hypotrochoid": Hypotrochoid,
    "basketweave": BasketWeave,
    "moire": MoirePattern,
    "sunburst": SunburstPattern,
    "linear_guilloche": LinearGuilloche,
    "spiral": SpiralPattern,
}


def create_pattern(pattern_type: str, params: Dict[str, Any] | None = None) -> PatternGenerator:
    cls = PATTERN_MAP.get(pattern_type)
    if cls is None:
        raise ValueError(f"Unknown pattern_type '{pattern_type}'")
    return cls(params or {})
