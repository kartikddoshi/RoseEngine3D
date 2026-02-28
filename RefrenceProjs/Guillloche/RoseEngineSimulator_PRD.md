
# 📝 Product Requirements Document: Digital Rose Engine Simulator

## 📌 1. Overview

### **Title:**  
Digital Rose Engine Simulator & G-code Generator

### **Purpose:**  
To create a precision software tool that simulates the mechanical behavior of a rose engine, enabling users to define cam and motion parameters, preview the resulting decorative patterns, and generate optimized G-code for CNC machining of intricate watch dials and similar applications.

## 🎯 2. Goals and Objectives

- Simulate complex guilloché-style patterns using parametric modeling of rose engine motion.
- Provide a live, vector-based visual preview of the pattern output.
- Convert the generated toolpaths into G-code for supported CNC machines.
- Offer fine-grained control over tolerances, tool parameters, and motion profiles.
- Ensure extensibility for custom cam/waveform profiles and machine configurations.

## 👥 3. Target Users

- Watch dial designers
- Guilloché and ornamental engravers
- CNC enthusiasts and machinists
- Jewelry and horology manufacturers
- Educational institutions teaching precision tooling

## 🧰 4. Functional Requirements

### 4.1 Input Parameter Configuration

| Parameter Group      | Details                                                                 |
|----------------------|-------------------------------------------------------------------------|
| **Cam/Waveform**     | Type (sine, cosine, elliptical, custom), lobes, amplitude, phase offset |
| **Spindle Motion**   | RPM, step indexing angle, angular velocity                              |
| **Tool Movement**    | Feed rate (mm/min), Z-depth, radial tool offset                         |
| **Material Settings**| User-defined presets for brass, steel, gold, etc.                       |
| **Tolerance Settings** | Micron-level control of deviation (±μm)                              |
| **Pattern Repeat**   | Number of pattern repetitions or revolutions                            |

### 4.2 Simulation Engine

#### Mathematical Modeling
- Use parametric equations to simulate rose engine movement:
  ```
  x(t) = A * sin(n * t + φ)
  y(t) = A * cos(n * t + φ)
  ```
- Composite waveforms for superimposed effects
- Rotation + oscillation path calculation per tool step

#### Vector Renderer
- Real-time SVG or WebGL rendering of the trace
- Visual toolpath overlay with start/end indicators
- Zoom, pan, and export as vector (SVG, DXF)

#### Precision Engine
- Floating point precision: 0.0001 mm
- Anti-aliasing for visual fidelity
- Optional pattern smoothing (Bezier fit or spline smoothing)

### 4.3 G-code Generator

#### G-code Structure
- G21 (mm), G90 (absolute mode)
- G1/G2/G3 interpolation with dynamic feed rate
- M-codes for spindle/tool handling (M3/M5)
- Configurable machine headers/footers

#### Post-Processor Support
- Built-in presets for:
  - GRBL
  - Mach3
  - LinuxCNC
  - Marlin
- Customizable post templates for other controllers

#### Safety Features
- Soft limits
- Min/max feed rate guards
- Dry-run flag option

### 4.4 File Management

| Feature         | Description                                            |
|-----------------|--------------------------------------------------------|
| Save Projects   | JSON or YAML based parameter snapshots                 |
| Export Pattern  | As vector (SVG/DXF)                                    |
| Export G-code   | .gcode / .nc file with metadata                        |
| Import Configs  | Load tool libraries, machine profiles                  |

## ⚙️ 5. Non-Functional Requirements

- **Platform**: Desktop (Windows/Linux/macOS), optionally WebAssembly
- **Performance**: Must handle ≥100k path points in <2s render time
- **Precision**: Floating-point accuracy ≥0.0001 mm
- **Security**: All offline processing unless cloud export is enabled
- **Extensibility**: Plugin-ready structure for waveform editors, scripting, or simulation enhancements

## 📈 6. Future Scope

- Custom waveform designer with spline editor or Fourier input
- 3D simulation of tool movement with rendered material removal
- Real-time streaming of G-code to machine (serial over USB)
- Support for rotary axis (4th axis)
- AI-powered pattern suggestions or analysis

## 📊 7. User Interface Requirements

### Layout:
1. **Parameter Panel** – Sidebar for inputs and sliders
2. **Live Preview** – Main canvas (vector or WebGL)
3. **Output Panel** – G-code export, toolpath stats
4. **Console/Log** – Warnings, simulation status, errors

### UI Features:
- Undo/redo support
- Reset to defaults
- Highlight regions of high tolerance deviation
- Dark mode for visual comfort

## 🔍 8. Validation & Testing Criteria

- Compare simulated toolpaths to real mechanical rose engine outputs
- Validate generated G-code with standard viewers (e.g., NC Viewer)
- Stress test parameter extremes (e.g., amplitude + tool offset)
- Cross-machine compatibility testing for post-processors

## 📅 9. Milestones (Example Timeline)

| Milestone                      | ETA       |
|-------------------------------|-----------|
| Math Engine + Core Params     | Week 2    |
| Live Preview & Rendering      | Week 4    |
| G-code Generator + PostProcs  | Week 6    |
| UI + Project Save/Load        | Week 8    |
| Testing & QA                  | Week 9–10 |
| Initial Release               | Week 12   |
