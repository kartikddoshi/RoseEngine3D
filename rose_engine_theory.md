# Rose Engine & Guilloché Mathematical Model & Architecture

This document tracks the initial implementation thinking, the mathematical theory underpinning the software, the desktop architecture utilized, and a walkthrough of the completed components.

## 1. Initial Implementation Thinking & Research

The primary objective is to recreate the intricate, microscopic overlapping cuts characteristic of traditional rose engine guilloché—as seen in Breguet watch dials and Fabergé eggs. Real guilloché relies on mechanical kinematics guided by complex cams (rosettes), rather than arbitrary splines.

A computational challenge arose: Simulating these continuous, sweeping arcs across 3D surfaces requires generating millions of vertices. A standard browser-based architecture or cloud-generated solution would either struggle with performance or accrue high server costs when attempting to compute and export high-resolution STLs or CNC G-code with jewelry-grade tolerances.

This led to the decision to shift to a **High-Performance Desktop Architecture** leveraging local computing power.

## 2. Desktop Architecture Implementation

To achieve the performance required for jewelry-grade resolution, the architecture is built on **Tauri + React + Three.js**.

- **Backend (Core Computational Engine in Rust):** 
  Offloads heavy trigonometry and clipping algorithms to native threads. It executes rapidly on the user's local CPU using multi-threading to calculate complex mathematical sequences.
- **Frontend (UI & 3D Visualization in React/TypeScript):** 
  Provides real-time rendering of the generated pattern via **React Three Fiber** (WebGL). The frontend remains lightweight by receiving pre-calculated buffers rather than computing the math itself.
- **Styling:** Custom glassmorphism interfaces built via **Tailwind CSS**.

## 3. The Mathematical Model: Kinematics & Trochoids

A true rose engine generates patterns by moving the headstock against a fixed cutting tool:
1. **Rocking Motion (Transverse):** The headstock pivots radially.
2. **Pumping Motion (Axial):** The headstock slides along the spindle axis, modifying cut depth.

The software models these using parametric equations for rolling circles.

### Epitrochoids (Rolling Outside)
Traced by a point attached to a circle of radius `r` rolling around the *outside* of a fixed circle of radius `R`.
*   `x(θ) = (R + r) cos(θ) - d cos(((R + r)/r)θ)`
*   `y(θ) = (R + r) sin(θ) - d sin(((R + r)/r)θ)`

### Hypotrochoids (Rolling Inside)
Traced by a point attached to a circle of radius `r` rolling around the *inside* of a fixed circle of radius `R`.
*   `x(θ) = (R - r) cos(θ) + d cos(((R - r)/r)θ)`
*   `y(θ) = (R - r) sin(θ) - d sin(((R - r)/r)θ)`

### Physical Parameters Map
Our numerical parameters directly map to physical lathe variables:

| Software Variable | Mathematical Equivalent | Physical Engine Equivalent | Function |
| :--- | :--- | :--- | :--- |
| `fixed_radius` | `R` | Base gear / Spindle center | Overall scale/location. |
| `rolling_radius` | `r` | Rosette wave count | Number of repeating elements. |
| `cam_amplitude` | `d` | Cam follower depth | "Wideness" of the loops. |
| `phase_shift` | `θ` offset | Crossing Wheel | Offsets cuts for basketweaves/moiré. |
| `cut_count` | N/A | Workpiece Rotations | Times the pattern is layered. |

## 4. Work Completed (Walkthrough)

The foundation of the desktop pattern generator has been successfully implemented and tested:

1. **Rust Kinematics Engine (`src-tauri/src/generator.rs`)**
   - Implements the mathematical models for Epitrochoids and Hypotrochoids.
   - Calculates overlapping multi-cut patterns (`PatternConfig`) that rotate around the workpiece automatically.
   
2. **3D Hardware Visualization (`src/components/PatternCanvas.tsx`)**
   - Displays the mathematically generated paths in an interactive 3D space using React Three Fiber boundaries (circular vs. rectangular).

3. **Premium Controller UI (`src/components/ParameterSidebar.tsx`)**
   - Provides exact slider-based controls mapping back to the mathematical parameters in Rust.

## 5. How to Run

To run the standalone desktop window locally:

```bash
npm run tauri dev
```

> [!TIP]
> The very first application boot may take a moment to assemble the WebGL frontend, but all subsequent pattern generations will compute nearly instantly using the underlying Rust MSVC toolchain!
