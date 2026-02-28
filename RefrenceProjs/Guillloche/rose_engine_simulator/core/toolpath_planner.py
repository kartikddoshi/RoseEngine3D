"""toolpath_planner.py

Adaptive tool-path sampling & 2-D → 3-D conversion.  For brevity we only
implement *polar → XY* with optional adaptive Δθ based on curvature; depth
mapping is deferred to `depth_mapper.py`.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np

from .pattern_generator import PatternGenerator, _to_mpf
import mpmath as mp

mp.mp.dps = 50 # Ensure consistency


def get_menger_curvature(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """Calculate Menger curvature for three 2D points."""
    # Ensure points are numpy arrays of float for np.linalg.norm
    p1_f = p1.astype(float)
    p2_f = p2.astype(float)
    p3_f = p3.astype(float)

    # Area of the triangle formed by p1, p2, p3 using the determinant formula (shoelace formula for area*2)
    # Using (x1(y2 − y3) + x2(y3 − y1) + x3(y1 − y2))/2
    # For robustness with mpf, convert to float for area calculation if points are small
    # Or, use cross product if points were 3D (p2-p1) x (p3-p1)
    area = 0.5 * abs(p1_f[0]*(p2_f[1] - p3_f[1]) + p2_f[0]*(p3_f[1] - p1_f[1]) + p3_f[0]*(p1_f[1] - p2_f[1]))

    # Lengths of the sides of the triangle
    a = np.linalg.norm(p2_f - p3_f)
    b = np.linalg.norm(p1_f - p3_f)
    c = np.linalg.norm(p1_f - p2_f)

    # Avoid division by zero if points are collinear or identical
    if a * b * c == 0.0:
        return 0.0  # Collinear points have zero Menger curvature
    
    # Menger curvature K = 4 * Area / (a * b * c)
    # Radius of circumcircle R = abc / (4 * Area)
    # Curvature K = 1/R
    curvature_val = (4 * area) / (a * b * c)
    return float(curvature_val)


def _simplify_collinear_points(points: np.ndarray, collinearity_tol: float = 1e-6) -> np.ndarray:
    """Removes redundant collinear points from a path.
    Tolerance is based on the cross product method (area of triangle).
    """
    if len(points) < 3:
        return points
    
    simplified_path = [points[0]]
    for i in range(1, len(points) - 1):
        p1 = points[i-1].astype(float)
        p2 = points[i].astype(float)
        p3 = points[i+1].astype(float)
        
        # Area of triangle * 2 = |(x1-x3)(y2-y1) - (x1-x2)(y3-y1)|
        # If area is close to zero, points are collinear.
        area_x2 = abs((p1[0] - p3[0]) * (p2[1] - p1[1]) - (p1[0] - p2[0]) * (p3[1] - p1[1]))
        if area_x2 > collinearity_tol:
            simplified_path.append(points[i])
            
    simplified_path.append(points[-1]) # Always keep the last point
    return np.array(simplified_path)


def generate_xy(
    pattern: PatternGenerator, 
    base_radius_mm: float = 0.0, 
    *, 
    start_angle_rad: float = 0.0,
    end_angle_rad: float = 2 * np.pi,
    angular_step_initial_rad: float = np.deg2rad(1.0), # Initial step, e.g., 1 degree
    min_angular_step_rad: float = np.deg2rad(0.01), # Min step to prevent infinite loop
    max_angular_step_rad: float = np.deg2rad(5.0),  # Max step to ensure detail
    curvature_tolerance: float = 0.005, # Tolerance for deviation from a straight line (related to sagitta)
    max_points: int = 20000,
    optimize_path: bool = True,
    collinearity_tol_simplify: float = 1e-5
) -> Tuple[np.ndarray, np.ndarray]:
    """Generates an adaptive XY toolpath for a given pattern.

    Args:
        pattern: The PatternGenerator instance.
        base_radius_mm: The base radius of the workpiece or pattern center.
        start_angle_rad: Starting angle for generation.
        end_angle_rad: Ending angle for generation.
        angular_step_initial_rad: Initial angular step size.
        min_angular_step_rad: Minimum angular step to prevent excessive refinement.
        max_angular_step_rad: Maximum angular step to avoid losing detail on flatter sections.
        curvature_tolerance: Controls how much the path can deviate. Smaller means more points.
                           This is more like a sagitta error tolerance.
        max_points: Maximum number of points to generate.
        optimize_path: If True, applies collinear point removal.
        collinearity_tol_simplify: Tolerance for collinear point simplification.

    Returns:
        Tuple of (x_coords, y_coords) as numpy arrays.
    """
    base_r_mpf = _to_mpf(base_radius_mm)
    current_theta_mpf = _to_mpf(start_angle_rad)
    end_theta_mpf = _to_mpf(end_angle_rad)
    d_theta_mpf = _to_mpf(angular_step_initial_rad)
    min_d_theta_mpf = _to_mpf(min_angular_step_rad)
    max_d_theta_mpf = _to_mpf(max_angular_step_rad)
    
    # Store points as list of mpf arrays initially for precision
    # Convert to float numpy arrays at the end for performance with other libs (e.g. plotting)
    path_points_mp = []

    # Initial point
    r_disp = pattern.radial(current_theta_mpf) # This is displacement
    total_r = base_r_mpf + r_disp
    x = total_r * mp.cos(current_theta_mpf)
    y = total_r * mp.sin(current_theta_mpf)
    path_points_mp.append(np.array([x, y])) # Storing as np.array of mpf objects

    # Second point to enable curvature calculation
    if current_theta_mpf < end_theta_mpf:
        current_theta_mpf = mp.fmin(current_theta_mpf + d_theta_mpf, end_theta_mpf)
        r_disp = pattern.radial(current_theta_mpf)
        total_r = base_r_mpf + r_disp
        x = total_r * mp.cos(current_theta_mpf)
        y = total_r * mp.sin(current_theta_mpf)
        path_points_mp.append(np.array([x, y]))

    idx = 0
    while current_theta_mpf < end_theta_mpf and len(path_points_mp) < max_points:
        idx +=1
        p1 = path_points_mp[-2] # Previous point
        p2 = path_points_mp[-1] # Current point

        # Propose next point with current d_theta
        theta_next_proposed = mp.fmin(current_theta_mpf + d_theta_mpf, end_theta_mpf)
        r_disp_next = pattern.radial(theta_next_proposed)
        total_r_next = base_r_mpf + r_disp_next
        x_next = total_r_next * mp.cos(theta_next_proposed)
        y_next = total_r_next * mp.sin(theta_next_proposed)
        p3_proposed = np.array([x_next, y_next])

        # Calculate deviation (approx. sagitta) from line segment p1-p3_proposed to p2
        # Using distance from point p2 to line segment p1-p3_proposed
        # More robust than raw curvature for step control in CNC context
        # Simplified: check distance of midpoint of p1-p3 to actual curve at midpoint theta
        # For adaptive sampling, a common method is to check sagitta error:
        # The distance between the midpoint of the chord (p1-p3_proposed) and the actual curve point at (theta_p1 + theta_p3_proposed)/2
        
        # Let's use a simpler check based on change in angle of the segment vectors
        # Or, stick to Menger curvature and adjust d_theta based on it.
        # For now, let's use Menger curvature. If p1, p2, p3_proposed are collinear, kappa is 0.
        kappa = get_menger_curvature(p1, p2, p3_proposed)
        
        # Heuristic: if curvature is high, reduce step size. If low, increase.
        # Target segment length L = R_curve / factor. d_theta ~ L / R_pattern
        # Or, error ~ L^2 * kappa / 8. We want error < tol.
        # So, L^2 < 8 * tol / kappa. L < sqrt(8 * tol / kappa).
        # d_theta_ideal ~ L / (base_r + r_disp)
        # This needs careful tuning.

        if kappa > 1e-9: # Avoid division by zero if perfectly flat
            # Desired arc length based on tolerance: L = sqrt(8 * curvature_tolerance / kappa)
            # This is an approximation of segment length for a given sagitta error
            desired_segment_length = mp.sqrt(8 * _to_mpf(curvature_tolerance) / _to_mpf(kappa))
            # Estimate current radius for d_theta calculation
            current_effective_radius = mp.fabs(base_r_mpf + pattern.radial(current_theta_mpf))
            if current_effective_radius < 1e-6: current_effective_radius = _to_mpf(1e-6) # Avoid div by zero
            
            d_theta_ideal = desired_segment_length / current_effective_radius

            if d_theta_mpf > d_theta_ideal * _to_mpf(1.2): # Current step too large
                d_theta_mpf = mp.fmax(d_theta_mpf * _to_mpf(0.75), min_d_theta_mpf) # Reduce step
                # Do not advance, recalculate with smaller d_theta_mpf
                if d_theta_mpf <= min_d_theta_mpf + _to_mpf(1e-9): # If at min step, accept and move on
                    # This case means we are at max refinement for this segment
                    pass # Will accept p3_proposed below
                else:
                    continue 
            elif d_theta_mpf < d_theta_ideal * _to_mpf(0.8): # Current step too small
                d_theta_mpf = mp.fmin(d_theta_mpf * _to_mpf(1.25), max_d_theta_mpf) # Increase step
        else: # Low or zero curvature, can increase step
            d_theta_mpf = mp.fmin(d_theta_mpf * _to_mpf(1.5), max_d_theta_mpf)

        # Accept the proposed point
        current_theta_mpf = theta_next_proposed
        path_points_mp.append(p3_proposed)

        if current_theta_mpf >= end_theta_mpf:
            break
            
    # Convert list of np.arrays (holding mpf) to a single 2D np.array of floats
    final_path_np = np.array([[float(p[0]), float(p[1])] for p in path_points_mp])

    if optimize_path and len(final_path_np) > 2:
        final_path_np = _simplify_collinear_points(final_path_np, collinearity_tol_simplify)
        
    return final_path_np[:, 0], final_path_np[:, 1]
