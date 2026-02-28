# Rose Engine Pattern Generator

A high-performance desktop application for generating and visualizing intricate guilloché patterns and rosettes, inspired by historical rose engine lathes used in high-end jewelry and luxury watch dial manufacturing.

## Overview

The **Rose Engine Pattern Generator** is a parametric 3D visualization tool built with **Rust**, **Tauri**, **React**, and **Three.js**. It simulates the kinematics of a physical rose engine lathe to produce mathematically accurate generative art, specifically tailored for subtractive manufacturing aesthetics.

Currently, the application acts as a fast and interactive visualization prototype. It computes exact cutting paths—including epitrochoids, hypotrochoids, Lissajous curves, and spirals—and renders them in real-time 3D space with premium metallic (PBR) finishes.

## Key Features

- **Four Mathematical Pattern Types**: Generate Trochoids, Rose Curves, Lissajous figures, and Spirals.
- **Real-Time 3D Visualization**: GPU-accelerated 3D WebGL rendering using React Three Fiber.
- **Parametric Engine Controls**: Adjust gear ratios (rolling and fixed radius), cam amplitudes, phase shifts, and spindle eccentricities.
- **Manufacturing Specifications**: Configure physical dimensions natively in millimeters (e.g., 32mm watch dial, inner bore diameters, plate thickness).
- **Zoned & Layered Patterns**: Create multi-zone designs with boundary clipping, mimicking real-world tool lift-off (Z-axis rapids).
- **Fast Rust Backend**: Pattern points are computed in parallel using Rust/Rayon, achieving <15ms generation times for complex multi-cut designs.
- **Exports**: Save designs as 2D vector `SVG` files or configuration `JSON` presets.

## Technology Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Zustand
- **3D Graphics**: Three.js, React Three Fiber
- **Backend**: Rust, Tauri
- **Parallel Computing**: Rayon (Rust)

## Getting Started

### Prerequisites

Ensure you have the following installed on your system:
- [Node.js](https://nodejs.org/) (v16+)
- [Rust](https://www.rust-lang.org/tools/install) (latest stable)
- Tauri dependencies for your specific OS.

### Installation & Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server with Tauri:**
   ```bash
   npm run tauri dev
   ```
   *Note: This will compile the Rust backend and launch the desktop application window.*

3. **Build for production:**
   ```bash
   npm run tauri build
   ```

## Roadmap

The ultimate goal of this project is to become a complete **computational manufacturing pipeline**. Planned upcoming features (Phase 3) include:

- **Solid Mesh Generation**: Converting 2D cut paths into real 3D V-groove subtractive boolean meshes.
- **STL Export**: Producing watertight binary STL files ready for CNC machining and 3D printing.
- **Manufacturing Simulation**: Simulating 60° V-tool cut profiles and toolpath g-code generation.

## License

This project is licensed under the MIT License.
