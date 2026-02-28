"""depth_mapper.py

Utility mapping radial/intensity values to depth-of-cut Z coordinates.
The depth profile is specified via parameters allowing:
  • absolute flat depth (legacy)
  • linear mapping (min_depth…max_depth)
  • Bézier/easing curve (future)
"""
from __future__ import annotations

from typing import Sequence, Callable, Optional, List, Tuple

import numpy as np
import mpmath as mp

mp.mp.dps = 50 # Ensure consistency

class DepthMapper:
    """Generates 3D toolpaths by adding Z-depth information, including multi-pass slicing."""

    def __init__(self,
                 total_depth_mm: float,
                 depth_per_pass_mm: float,
                 safe_z_mm: float,
                 material_top_z_mm: float = 0.0,
                 feed_rate_plunge_mm_min: Optional[float] = None):
        """
        Args:
            total_depth_mm: Final target depth from material_top_z (positive value means cutting down).
            depth_per_pass_mm: Maximum depth for each cutting pass (positive value).
            safe_z_mm: Z height for rapid moves (absolute Z coordinate).
            material_top_z_mm: Absolute Z coordinate of the material surface.
            feed_rate_plunge_mm_min: Specific feed rate for Z plunge moves, if desired.
        """
        if total_depth_mm <= 0:
            raise ValueError("Total depth must be positive.")
        if depth_per_pass_mm <= 0:
            raise ValueError("Depth per pass must be positive.")

        self.total_depth_mm = mp.mpf(str(total_depth_mm))
        self.depth_per_pass_mm = mp.mpf(str(depth_per_pass_mm))
        self.safe_z_mm = mp.mpf(str(safe_z_mm))
        self.material_top_z_mm = mp.mpf(str(material_top_z_mm))
        self.feed_rate_plunge_mm_min = mp.mpf(str(feed_rate_plunge_mm_min)) if feed_rate_plunge_mm_min else None

        self.num_passes = int(mp.ceil(self.total_depth_mm / self.depth_per_pass_mm))
        if self.num_passes == 0 and self.total_depth_mm > 0: # Ensure at least one pass if depth is non-zero
             self.num_passes = 1

    def _calculate_pass_depths(self) -> List[mp.mpf]:
        """Calculates the Z depth for each cutting pass."""
        pass_depths = []
        current_pass_depth_offset = mp.mpf(0)
        for i in range(self.num_passes):
            current_pass_depth_offset = min((i + 1) * self.depth_per_pass_mm, self.total_depth_mm)
            pass_depths.append(self.material_top_z_mm - current_pass_depth_offset)
        return pass_depths

    def generate_3d_path_for_pass(
        self,
        xy_points: np.ndarray, # Nx2 array of X, Y floats
        pass_z: mp.mpf,
        is_first_pass: bool
    ) -> List[Tuple[float, float, float, Optional[float], str]]: # X, Y, Z, Feed, Type ('rapid'/'cut'/'plunge')
        """Generates a 3D path for a single Z-depth pass.
        Includes lead-in and lead-out moves.
        """
        path_3d_pass = []
        num_xy_points = xy_points.shape[0]

        if num_xy_points == 0:
            return []

        # 1. Rapid to safe Z above the first point
        path_3d_pass.append((float(xy_points[0, 0]), float(xy_points[0, 1]), float(self.safe_z_mm), None, "rapid_z_safe"))

        # 2. Plunge to current pass_z (or material_top_z if first engagement of first pass)
        #    If it's the very first point of the very first pass, plunge to material_top_z first, then to pass_z.
        #    This can be handled by the G-code engine more explicitly with pecking/slower plunge for first entry.
        #    Here, we just specify the target Z for the plunge.
        plunge_feed = self.feed_rate_plunge_mm_min if self.feed_rate_plunge_mm_min else None
        path_3d_pass.append((float(xy_points[0, 0]), float(xy_points[0, 1]), float(pass_z), plunge_feed, "plunge"))

        # 3. Cut along the XY path at current pass_z
        for i in range(num_xy_points):
            path_3d_pass.append((float(xy_points[i, 0]), float(xy_points[i, 1]), float(pass_z), None, "cut"))

        # 4. Retract to safe Z from the last point
        if num_xy_points > 0:
            path_3d_pass.append((float(xy_points[-1, 0]), float(xy_points[-1, 1]), float(self.safe_z_mm), None, "retract_z_safe"))
        
        return path_3d_pass

    def generate_multi_pass_3d_toolpath(
        self,
        xy_points: np.ndarray # Nx2 array of X, Y floats
    ) -> List[Tuple[float, float, float, Optional[float], str]]: # X, Y, Z, Feed, Type
        """Generates a full 3D toolpath with multiple Z passes.
        Each element is (x, y, z, feed_rate, move_type_tag).
        Move types: 'rapid_z_safe', 'plunge', 'cut', 'retract_z_safe'.
        Feed rate is None if it should use the default cutting feed rate.
        """
        if xy_points.shape[0] == 0:
            return []

        pass_depths_z = self._calculate_pass_depths()
        full_3d_toolpath = []

        for i, pass_z_level in enumerate(pass_depths_z):
            is_first_pass_overall = (i == 0)
            pass_toolpath = self.generate_3d_path_for_pass(xy_points, pass_z_level, is_first_pass_overall)
            full_3d_toolpath.extend(pass_toolpath)
            
            # Optional: Add a full retract to safe_z and rapid to start of next pass if passes are not linked
            # For continuous engraving, this might not be needed if the tool stays down.
            # However, for clarity and safety between depth changes, it's good practice.
            # The current generate_3d_path_for_pass already includes retract and plunge.

        return full_3d_toolpath

# Example Usage (for testing if run directly):
if __name__ == '__main__':
    # Define a simple square path
    example_xy = np.array([
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
        [0, 0]
    ])

    mapper = DepthMapper(
        total_depth_mm=0.5,
        depth_per_pass_mm=0.2,
        safe_z_mm=5.0,
        material_top_z_mm=0.0,
        feed_rate_plunge_mm_min=50.0
    )

    print(f"Number of passes: {mapper.num_passes}")
    pass_depths = mapper._calculate_pass_depths()
    print(f"Pass depths (absolute Z): {pass_depths}")

    full_toolpath = mapper.generate_multi_pass_3d_toolpath(example_xy)

    print("\nGenerated 3D Toolpath:")
    for point in full_toolpath:
        print(f"X={point[0]:.2f}, Y={point[1]:.2f}, Z={point[2]:.2f}, F={point[3] if point[3] else '-'}, Type={point[4]}")

    # Test with zero depth
    try:
        mapper_zero_depth = DepthMapper(0, 0.1, 5.0)
    except ValueError as e:
        print(f"\nError for zero depth: {e}")

    # Test with single pass
    mapper_single_pass = DepthMapper(
        total_depth_mm=0.1,
        depth_per_pass_mm=0.2,
        safe_z_mm=5.0
    )
    print(f"\nSingle pass (num_passes): {mapper_single_pass.num_passes}")
    single_pass_toolpath = mapper_single_pass.generate_multi_pass_3d_toolpath(example_xy)
    print("\nGenerated Single Pass 3D Toolpath (first 10 points):")
    for point in single_pass_toolpath[:10]:
        print(f"X={point[0]:.2f}, Y={point[1]:.2f}, Z={point[2]:.2f}, F={point[3] if point[3] else '-'}, Type={point[4]}")


# Legacy function (can be kept for compatibility or removed if class is preferred)
# def map_depth(r: Sequence[float], base_depth: float | None = None, *, profile: str = "flat",
#               min_depth: float = -0.01, max_depth: float = -0.05) -> np.ndarray:
#     """Return an array of Z values the same shape as *r*.
#     Parameters
#     ----------
#     r : radial values (any shape convertible to ndarray)
#     base_depth : if given, ignore *profile* and return constant depth.
#     profile : "flat" | "linear"
#         Mapping type when *base_depth* is None.
#     min_depth, max_depth : depths for linear mapping (min→radius min, max→radius max).
#     """
#     r_arr = np.asarray(r, dtype=float)
#     if base_depth is not None:
#         return np.full_like(r_arr, base_depth, dtype=float)

#     if profile == "linear":
#         # normalise r to 0…1
#         r_norm = (r_arr - r_arr.min()) / (r_arr.ptp() + 1e-12)
#         return min_depth + r_norm * (max_depth - min_depth)
#     # default flat
#     return np.full_like(r_arr, max_depth, dtype=float)
