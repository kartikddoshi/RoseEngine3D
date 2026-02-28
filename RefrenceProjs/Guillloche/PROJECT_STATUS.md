# Digital Rose Engine Simulator – Project Status (May 24 2025)

## 🎯 Objectives
| Area | Key Goals |
|------|-----------|
| **Pattern Generation** | • Wide library: simple/compound rosettes, linear, spiral, basket-weave, sunburst, moiré, epitrochoids, hypotrochoids, custom harmonic blends<br>• High-precision maths (mpmath) with adaptive sampling<br>• Depth-mapping for 3-D relief |
| **Rosette Library** | Preload standard tooth counts (12–120) and allow user-defined eccentric / profile files |
| **Tool-Path & G-code** | • Optimised XY paths (min curvature, min air moves)<br>• Z multi-pass, material/tool aware<br>• Output for GRBL, Mach3; extendable to Fanuc/Haas |
| **3-D Visualisation** | Real-time OpenGL preview, STL export, cross-sections |
| **GUI** | Parameter designer, material selector, live preview, export buttons |
| **Testing & Quality** | ≥90 % unit coverage, mypy strict, CI workflow |
| **Docs & Packaging** | MkDocs site, README examples, PyPI release |

---

## ✅ Progress so far
| Date | Milestone |
|------|-----------|
| Earlier | Initial PyQt app skeleton, basic `MathModel`, basic G-code generator |
| Prev sessions | • Fixed multiple mp.mpf TypeErrors<br>• Added numerous pattern functions (sine, cosine, epi/hypo-trochoids, custom harmonic) |
| *Today* | • Introduced **modular core**:
  • `pattern_generator.py` – class-based, composable patterns  
  • `rosette_library.py` – JSON-backed registry (12-120 teeth)  
  • `toolpath_planner.py` – curvature-adaptive θ-sampling  
  • `depth_mapper.py` – flat/linear depth profiles  
  • Extended `MathModel` with `generate_toolpath_adaptive()`  
  • Minor tweak: float centre to keep arrays numeric |

---

## 🔜 Next Steps (Phase 1 ⇢ Phase 2 bridge)
1. **GUI Integration**
   * Switch *MainWindow* & *Preview3DWidget* to call `generate_toolpath_adaptive`.
   * Populate pattern ComboBoxes from `pattern_generator.PATTERN_MAP`.
   * Expose depth-profile choices (flat/linear) & rosette selection.
2. **Tool-Path Optimiser**
   * Implement 2-opt / arc-fit segment merge inside `toolpath_planner`.
   * Add `toolpath_planner.generate_xy(..., optimise=True)` flag.
3. **G-code Engine v2**
   * Migrate `gcode/generator.py` → `gcode/engine.py` with Jinja2 templates.
   * Support multi-pass Z slicing automatically (`depth_mapper` + tool settings).
4. **Material & Tool Profiles**
   * Create `utils/material_profile.py`; feed default feeds/speeds automatically.
5. **Unit Tests & CI**
   * Add pytest suites for pattern maths, adaptive sampler, depth mapping.
   * GitHub Actions workflow (windows+linux).  Target ≥70 % coverage initially.
6. **Documentation**
   * Auto-generate pattern gallery (Matplotlib) in `docs/`.

---

## 🚀 Longer-Term Roadmap
| Phase | Deliverables |
|-------|--------------|
| **Phase 2** (2 wks) | • Advanced optimiser, depth mapper smoothing, STL output  
  • Extended rosette JSON (eccentric, custom profile curves)  
  • Material & tool parameter UI
| **Phase 3** (2 wks) | • Full GUI polish: drag-drop pattern composer, live FPS>30 preview  
  • Cross-section viewer, measurement tools, undo/redo system
| **Phase 4** (1 wk) | • Comprehensive tests (≥90 %), docs, packaging, real-machine G-code validation

---

## ℹ️ Open Questions / Decisions
* Depth profile curves: simple linear vs Bézier-based easing?  
* Which external back-plotter to bundle for G-code verification?  
* Add GPU compute (cupy) for ultra-dense patterns?

---

*Maintained by Cascade AI – last update: 2025-05-24 13:46 IST*
