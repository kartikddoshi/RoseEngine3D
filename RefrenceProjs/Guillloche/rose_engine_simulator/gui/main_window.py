import sys
import os
import numpy as np
import traceback # Added
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDockWidget, QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox, QTabWidget,
    QGroupBox, QSplitter, QFileDialog, QMessageBox, QTextEdit, QToolBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QAction, QIcon

# Import our custom modules
from rose_engine_simulator.core.math_model import MathModel
from rose_engine_simulator.core.pattern_generator import PATTERN_MAP
from rose_engine_simulator.core.toolpath_planner import ToolpathPlanner # Added
from rose_engine_simulator.core.depth_mapper import DepthMapper       # Added
from rose_engine_simulator.gcode.engine import GCodeEngine           # Updated from generator to engine
from rose_engine_simulator.gui.preview_3d import Preview3DWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Rose Engine Simulator")
        self.setGeometry(100, 100, 1200, 800) # Increased size for more UI elements
        
        # Create the math model and G-code engine
        self.math_model = MathModel()
        self.gcode_engine = GCodeEngine() # Updated
        
        # Initialize the UI
        self.init_ui()
        
        # Connect signals and slots
        self.connect_signals()
        
        # Default pattern parameters optimized for small-scale (5mm) engraving
        self.apply_default_parameters()

        # Call on_pattern_type_changed initially to set correct UI state for default pattern
        default_pattern_key = list(PATTERN_MAP.keys())[0] if PATTERN_MAP else "standard"
        if default_pattern_key in [self.pattern_type_combo.itemText(i) for i in range(self.pattern_type_combo.count())]:
            self.pattern_type_combo.setCurrentText(default_pattern_key)
        self.on_pattern_type_changed(self.pattern_type_combo.currentText()) # Use current text after ensuring it's valid

    def init_ui(self):
        """Initialize the user interface components."""
        # Set central widget as a splitter for flexible layout
        self.central_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.central_splitter)
        
        # --- Left Side: Parameter Panel ---
        self.parameter_widget = QWidget()
        self.parameter_layout = QVBoxLayout(self.parameter_widget)
        
        # Create parameter tabs for organization
        self.param_tabs = QTabWidget()
        
        # Tab 1: Pattern Parameters
        self.pattern_tab = QWidget()
        self.pattern_layout = QFormLayout(self.pattern_tab)
        
        # Pattern type selection
        self.pattern_type_combo = QComboBox()
        self.pattern_type_combo.addItems(list(PATTERN_MAP.keys())) # Use PATTERN_MAP
        self.pattern_layout.addRow(QLabel("Pattern Type:"), self.pattern_type_combo)
        
        # Basic pattern parameters group (now an instance variable)
        self.standard_pattern_group = QGroupBox("Pattern Parameters")
        pattern_form = QFormLayout(self.standard_pattern_group)
        
        # For small-scale work, we use smaller default values
        self.cam_amplitude_spinbox = QDoubleSpinBox()
        self.cam_amplitude_spinbox.setRange(0.01, 2.0)  # Max 2mm for small work
        self.cam_amplitude_spinbox.setSingleStep(0.01)  # 0.01mm steps for precision
        self.cam_amplitude_spinbox.setValue(0.5)        # Default 0.5mm
        self.cam_amplitude_spinbox.setSuffix(" mm")
        self.cam_amplitude_spinbox.setDecimals(3)       # 3 decimal places (micron precision)
        pattern_form.addRow(QLabel("Amplitude:"), self.cam_amplitude_spinbox)
        
        self.cam_lobes_spinbox = QSpinBox()
        self.cam_lobes_spinbox.setRange(1, 100)
        self.cam_lobes_spinbox.setValue(6)              # Default 6 lobes
        pattern_form.addRow(QLabel("Lobes:"), self.cam_lobes_spinbox)
        
        self.cam_phase_offset_spinbox = QDoubleSpinBox()
        self.cam_phase_offset_spinbox.setRange(0, 360.0)
        self.cam_phase_offset_spinbox.setSingleStep(1.0)
        self.cam_phase_offset_spinbox.setValue(0.0)
        self.cam_phase_offset_spinbox.setSuffix(" °")
        pattern_form.addRow(QLabel("Phase Offset:"), self.cam_phase_offset_spinbox)
        
        self.base_radius_spinbox = QDoubleSpinBox()
        self.base_radius_spinbox.setRange(0.1, 10.0)
        self.base_radius_spinbox.setSingleStep(0.1)
        self.base_radius_spinbox.setValue(2.0)           # Default 2mm for small work
        self.base_radius_spinbox.setSuffix(" mm")
        self.base_radius_spinbox.setDecimals(3)          # 3 decimal places
        pattern_form.addRow(QLabel("Base Radius:"), self.base_radius_spinbox)
        
        # Add the pattern group to the layout
        self.pattern_layout.addRow(self.standard_pattern_group)

        # Group for Custom Harmonic definitions
        self.harmonic_group = QGroupBox("Custom Harmonic Definition")
        self.harmonic_group_layout = QVBoxLayout(self.harmonic_group) # Main layout for this group
        
        self.harmonics_input_area_layout = QFormLayout() # For rows of harmonic inputs
        self.harmonic_group_layout.addLayout(self.harmonics_input_area_layout)
        
        harmonic_buttons_layout = QHBoxLayout()
        self.add_harmonic_button = QPushButton("Add Harmonic Component")
        self.remove_harmonic_button = QPushButton("Remove Last Harmonic")
        harmonic_buttons_layout.addWidget(self.add_harmonic_button)
        harmonic_buttons_layout.addWidget(self.remove_harmonic_button)
        self.harmonic_group_layout.addLayout(harmonic_buttons_layout)
        
        self.pattern_layout.addRow(self.harmonic_group)
        self.harmonic_group.setVisible(False) # Initially hidden

        # Store dynamic harmonic input rows
        self.harmonic_input_rows = [] # List to store (amp_spin, lobes_spin, phase_spin) tuples
        
        # Tab 2: Workpiece & Tool Parameters
        self.tool_tab = QWidget()
        self.tool_layout = QFormLayout(self.tool_tab)
        
        # Workpiece parameters group
        workpiece_group = QGroupBox("Workpiece")
        workpiece_form = QFormLayout(workpiece_group)
        
        self.workpiece_diameter_spinbox = QDoubleSpinBox()
        self.workpiece_diameter_spinbox.setRange(1.0, 50.0)
        self.workpiece_diameter_spinbox.setSingleStep(0.1)
        self.workpiece_diameter_spinbox.setValue(5.0)  # Default 5mm diameter
        self.workpiece_diameter_spinbox.setSuffix(" mm")
        workpiece_form.addRow(QLabel("Diameter:"), self.workpiece_diameter_spinbox)
        
        self.workpiece_thickness_spinbox = QDoubleSpinBox()
        self.workpiece_thickness_spinbox.setRange(0.1, 5.0)
        self.workpiece_thickness_spinbox.setSingleStep(0.1)
        self.workpiece_thickness_spinbox.setValue(0.5)  # Default 0.5mm thickness
        self.workpiece_thickness_spinbox.setSuffix(" mm")
        workpiece_form.addRow(QLabel("Thickness:"), self.workpiece_thickness_spinbox)
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(["brass", "silver", "aluminum", "gold"])
        workpiece_form.addRow(QLabel("Material:"), self.material_combo)
        
        # Tool parameters group
        tool_group = QGroupBox("Tool")
        tool_form = QFormLayout(tool_group)
        
        self.tool_type_combo = QComboBox()
        self.tool_type_combo.addItems(["ball_0.1mm", "v_bit_30deg", "flat_0.2mm"])
        tool_form.addRow(QLabel("Tool Type:"), self.tool_type_combo)
        
        self.z_depth_spinbox = QDoubleSpinBox()
        self.z_depth_spinbox.setRange(-1.0, 0.0)
        self.z_depth_spinbox.setSingleStep(0.01)
        self.z_depth_spinbox.setValue(-0.05)  # Default 0.05mm depth
        self.z_depth_spinbox.setSuffix(" mm")
        self.z_depth_spinbox.setDecimals(3)   # 3 decimal places
        tool_form.addRow(QLabel("Cut Depth:"), self.z_depth_spinbox)
        
        self.num_passes_spinbox = QSpinBox()
        self.num_passes_spinbox.setRange(1, 10)
        self.num_passes_spinbox.setValue(3)  # Default 3 passes
        tool_form.addRow(QLabel("Number of Passes:"), self.num_passes_spinbox)
        
        # Add the groups to the layout
        self.tool_layout.addRow(workpiece_group)
        self.tool_layout.addRow(tool_group)
        
        # Tab 3: Advanced Parameters
        self.advanced_tab = QWidget()
        self.advanced_layout = QFormLayout(self.advanced_tab)
        
        self.tolerance_spinbox = QDoubleSpinBox()
        self.tolerance_spinbox.setRange(0.0001, 0.1)
        self.tolerance_spinbox.setSingleStep(0.0001)
        self.tolerance_spinbox.setValue(0.001)  # Default 0.001mm (1 micron)
        self.tolerance_spinbox.setSuffix(" mm")
        self.tolerance_spinbox.setDecimals(4)    # 4 decimal places
        self.advanced_layout.addRow(QLabel("Tolerance:"), self.tolerance_spinbox)
        
        self.points_spinbox = QSpinBox()
        self.points_spinbox.setRange(100, 20000)
        self.points_spinbox.setSingleStep(100)
        self.points_spinbox.setValue(1000)  # Default 1000 points
        self.advanced_layout.addRow(QLabel("Path Points:"), self.points_spinbox)
        
        # Add tabs to the tab widget
        self.param_tabs.addTab(self.pattern_tab, "Pattern")
        self.param_tabs.addTab(self.tool_tab, "Workpiece & Tool")
        self.param_tabs.addTab(self.advanced_tab, "Advanced")

        # Tab 4: G-code Settings
        self.gcode_settings_tab = QWidget()
        self.gcode_settings_layout = QFormLayout(self.gcode_settings_tab)

        self.safe_z_mm_spinbox = QDoubleSpinBox()
        self.safe_z_mm_spinbox.setRange(0.1, 100.0)
        self.safe_z_mm_spinbox.setSingleStep(0.1)
        self.safe_z_mm_spinbox.setValue(5.0)
        self.safe_z_mm_spinbox.setSuffix(" mm")
        self.gcode_settings_layout.addRow(QLabel("Safe Z Height:"), self.safe_z_mm_spinbox)

        self.default_feed_rate_spinbox = QDoubleSpinBox()
        self.default_feed_rate_spinbox.setRange(1, 5000.0)
        self.default_feed_rate_spinbox.setSingleStep(10)
        self.default_feed_rate_spinbox.setValue(150.0)
        self.default_feed_rate_spinbox.setSuffix(" mm/min")
        self.gcode_settings_layout.addRow(QLabel("Default Cut Feed Rate:"), self.default_feed_rate_spinbox)

        self.plunge_feed_rate_spinbox = QDoubleSpinBox()
        self.plunge_feed_rate_spinbox.setRange(1, 1000.0)
        self.plunge_feed_rate_spinbox.setSingleStep(5)
        self.plunge_feed_rate_spinbox.setValue(50.0)
        self.plunge_feed_rate_spinbox.setSuffix(" mm/min")
        self.gcode_settings_layout.addRow(QLabel("Plunge Feed Rate:"), self.plunge_feed_rate_spinbox)

        self.spindle_rpm_spinbox = QSpinBox()
        self.spindle_rpm_spinbox.setRange(100, 30000)
        self.spindle_rpm_spinbox.setSingleStep(100)
        self.spindle_rpm_spinbox.setValue(3000)
        self.gcode_settings_layout.addRow(QLabel("Spindle RPM:"), self.spindle_rpm_spinbox)
        
        self.tool_number_spinbox = QSpinBox()
        self.tool_number_spinbox.setRange(0, 99)
        self.tool_number_spinbox.setValue(1)
        self.gcode_settings_layout.addRow(QLabel("Tool Number (T):"), self.tool_number_spinbox)

        self.coolant_checkbox = QComboBox()
        self.coolant_checkbox.addItems(["Off", "Mist (M7)", "Flood (M8)"])
        self.gcode_settings_layout.addRow(QLabel("Coolant:"), self.coolant_checkbox)

        self.param_tabs.addTab(self.gcode_settings_tab, "G-code Settings")

        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Parameters")
        self.apply_button.setToolTip("Apply current parameters to the preview")
        button_layout.addWidget(self.apply_button)
        
        self.generate_button = QPushButton("Generate G-code")
        self.generate_button.setToolTip("Generate G-code based on current parameters")
        button_layout.addWidget(self.generate_button)

        # Add parameter panel to the left side of the splitter
        self.parameter_layout.addWidget(self.param_tabs)
        self.parameter_layout.addLayout(button_layout)
        self.central_splitter.addWidget(self.parameter_widget)

        # --- Right Side: 3D Preview and G-code Output ---
        self.right_panel_widget = QWidget()
        self.right_panel_layout = QVBoxLayout(self.right_panel_widget)

        # Create a tab widget for Preview and G-code output
        self.output_tabs = QTabWidget()

        # 3D Preview Widget (already exists as a class member)
        self.preview_widget = Preview3DWidget(self.math_model)
        self.output_tabs.addTab(self.preview_widget, "3D Preview")

        # G-code Output Area
        self.gcode_output_widget = QWidget()
        self.gcode_output_layout = QVBoxLayout(self.gcode_output_widget)
        self.gcode_output_textedit = QTextEdit()
        self.gcode_output_textedit.setReadOnly(True)
        self.gcode_output_textedit.setFontFamily("Courier New")
        self.gcode_output_layout.addWidget(self.gcode_output_textedit)
        
        self.save_gcode_button = QPushButton("Save G-code to File...")
        self.gcode_output_layout.addWidget(self.save_gcode_button)
        self.output_tabs.addTab(self.gcode_output_widget, "G-code Output")

        self.right_panel_layout.addWidget(self.output_tabs)
        self.central_splitter.addWidget(self.right_panel_widget)

        # Set initial splitter sizes (adjust as needed)
        self.central_splitter.setSizes([400, 800]) # Parameter panel width, preview/gcode width

        # --- Toolbar (Placeholder for future actions) ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16,16))
        self.addToolBar(toolbar)
        # Example actions (to be implemented)
        # open_action = QAction(QIcon.fromTheme("document-open"), "Open Parameters...", self)
        # save_action = QAction(QIcon.fromTheme("document-save"), "Save Parameters...", self)
        # toolbar.addAction(open_action)
        # toolbar.addAction(save_action)

        # Initialize dynamic harmonic inputs
        self._update_harmonic_inputs_visibility()
        if not self.harmonic_input_rows: # Add one by default if custom harmonic is selected and none exist
            self.add_harmonic_input_row() # Add one initial row for harmonics

        self.generate_button.setToolTip("Generate G-code from current pattern")
        button_layout.addWidget(self.generate_button)
        
        # Add tab widget and buttons to parameter layout
        self.parameter_layout.addWidget(self.param_tabs)
        self.parameter_layout.addLayout(button_layout)
        
        # --- Right Side: Preview & Output ---
        self.preview_output_widget = QWidget()
        self.preview_output_layout = QVBoxLayout(self.preview_output_widget)
        
        # Create the 3D preview widget
        self.preview_3d = Preview3DWidget()
        self.preview_3d.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Output area for G-code display
        self.output_group = QGroupBox("G-code Output")
        output_layout = QVBoxLayout(self.output_group)
        
        self.gcode_output = QTextEdit()
        self.gcode_output.setReadOnly(True)
        self.gcode_output.setMinimumHeight(100)
        output_layout.addWidget(self.gcode_output)
        
        output_button_layout = QHBoxLayout()
        self.save_gcode_button = QPushButton("Save G-code")
        self.save_gcode_button.setEnabled(False)  # Disabled until G-code is generated
        output_button_layout.addWidget(self.save_gcode_button)
        output_layout.addLayout(output_button_layout)
        
        # Add preview and output to layout
        self.preview_output_layout.addWidget(self.preview_3d, stretch=4)
        self.preview_output_layout.addWidget(self.output_group, stretch=1)
        
        # Add widgets to splitter
        self.central_splitter.addWidget(self.parameter_widget)
        self.central_splitter.addWidget(self.preview_output_widget)
        self.central_splitter.setSizes([300, 900])  # Default sizes
        
        # Create menus and toolbars
        self.create_menus()
        
        # Status bar for messages
        self.statusBar().showMessage("Ready")

    def create_menus(self):
        """Create the application menus and toolbar."""
        # Main menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        save_gcode_action = QAction("&Save G-code...", self)
        save_gcode_action.setShortcut("Ctrl+S")
        save_gcode_action.setStatusTip("Save generated G-code to file")
        save_gcode_action.triggered.connect(self.save_gcode)
        file_menu.addAction(save_gcode_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        reset_view_action = QAction("&Reset View", self)
        reset_view_action.setStatusTip("Reset the 3D preview camera")
        reset_view_action.triggered.connect(self.reset_preview)
        view_menu.addAction(reset_view_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show information about the application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        toolbar.addAction(save_gcode_action)
        toolbar.addSeparator()
        toolbar.addAction(reset_view_action)
    
    def _add_harmonic_input_row(self):
        """Adds a new row of input fields for a single harmonic component."""
        row_count = self.harmonics_input_area_layout.rowCount()
        group_box = QGroupBox(f"Harmonic {row_count + 1}")
        group_box_layout = QFormLayout(group_box)

        amp_spin = QDoubleSpinBox()
        amp_spin.setRange(0.001, 5.0) # Max 5mm amplitude for a component
        amp_spin.setSingleStep(0.01)
        amp_spin.setValue(0.1) # Default component amplitude
        amp_spin.setSuffix(" mm")
        amp_spin.setDecimals(3)
        group_box_layout.addRow(QLabel("Amplitude:"), amp_spin)

        lobes_spin = QSpinBox()
        lobes_spin.setRange(1, 200) # More lobes for components
        lobes_spin.setValue(3)
        group_box_layout.addRow(QLabel("Lobes:"), lobes_spin)

        phase_spin = QDoubleSpinBox()
        phase_spin.setRange(0, 360.0)
        phase_spin.setSingleStep(1.0)
        phase_spin.setValue(0.0)
        phase_spin.setSuffix(" °")
        group_box_layout.addRow(QLabel("Phase Offset:"), phase_spin)
        
        self.harmonics_input_area_layout.addRow(group_box)
        self.harmonic_input_rows.append({'group_box': group_box, 'amp': amp_spin, 'lobes': lobes_spin, 'phase': phase_spin})

    def _remove_last_harmonic_input_row(self):
        """Removes the last added harmonic component input row."""
        if not self.harmonic_input_rows:
            return

        last_row_widgets = self.harmonic_input_rows.pop()
        group_box_to_remove = last_row_widgets['group_box']
        
        # Iterate through items in harmonics_input_area_layout to find and remove the groupbox
        for i in range(self.harmonics_input_area_layout.rowCount()):
            item = self.harmonics_input_area_layout.itemAt(i, QFormLayout.ItemRole.SpanningRole) # QFormLayout.SpanningRole for QGroupBox
            if item and item.widget() == group_box_to_remove:
                # Remove the entire row (label and field) associated with the groupbox
                self.harmonics_input_area_layout.removeRow(i)
                break # Exit loop once removed
        
        group_box_to_remove.deleteLater() # Ensure proper cleanup of the groupbox and its children

    @pyqtSlot(str)
    def on_pattern_type_changed(self, pattern_name):
        """Handles changes in the selected pattern type to show/hide relevant UI elements."""
        if pattern_name == "custom_harmonic":
            self.standard_pattern_group.setVisible(False)
            self.harmonic_group.setVisible(True)
            if not self.harmonic_input_rows: # If no rows exist, add one by default
                self._add_harmonic_input_row()
        else:
            self.standard_pattern_group.setVisible(True)
            self.harmonic_group.setVisible(False)

    def connect_signals(self):
        """Connect signals from UI elements to their respective slots."""
        # Connect the Apply button
        self.apply_button.clicked.connect(self.apply_parameters)
        
        # Connect the Generate G-code button
        self.generate_button.clicked.connect(self.on_generate_gcode_clicked) # Corrected to new handler
        
        # Connect the Save G-code button
        # The self.save_gcode_button is part of the gcode_output_widget, ensure it's connected.
        # It seems there might be two save_gcode_button instances from the view_file output.
        # I will connect the one that is part of the gcode_output_widget (the QTextEdit area).
        # If self.save_gcode_button was defined earlier for the toolbar/menu, that's handled by self.save_gcode.
        # This connection is for the button directly under the G-code text output area.
        if hasattr(self, 'gcode_output_widget') and hasattr(self.gcode_output_widget.layout().itemAt(1).widget(), 'clicked'): # Check if button exists
             self.gcode_output_widget.layout().itemAt(1).widget().clicked.connect(self.on_save_gcode_clicked) # Connect the button under text area
        else: # Fallback if the specific button isn't found as expected, connect the general one if it exists
            if hasattr(self, 'save_gcode_button'):
                 self.save_gcode_button.clicked.connect(self.on_save_gcode_clicked)

        # Connect pattern type change to handler
        self.pattern_type_combo.currentTextChanged.connect(self.on_pattern_type_changed)
        
        # Connect harmonic add/remove buttons
        if hasattr(self, 'add_harmonic_button'): # Check if these buttons exist
            self.add_harmonic_button.clicked.connect(self._add_harmonic_input_row) # Assuming method name consistency
        if hasattr(self, 'remove_harmonic_button'):
            self.remove_harmonic_button.clicked.connect(self._remove_last_harmonic_input_row) # Assuming method name consistency


        # Custom harmonic UI signals
        self.pattern_type_combo.currentTextChanged.connect(self.on_pattern_type_changed)
        self.add_harmonic_button.clicked.connect(self._add_harmonic_input_row)
        self.remove_harmonic_button.clicked.connect(self._remove_last_harmonic_input_row)
    
    def apply_default_parameters(self):
        """Apply default parameters optimized for small-scale guilloche."""
        # Apply the default parameters to the math model
        params = {
            'cam_amplitude': 0.5,      # 0.5mm amplitude
            'cam_lobes': 6,            # 6 lobes
            'cam_phase_offset': 0,     # No phase offset
            'base_radius': 2.0,        # 2mm radius
            'z_depth': -0.05,          # 0.05mm depth
            'workpiece_diameter': 5.0, # 5mm diameter workpiece
            'workpiece_thickness': 0.5 # 0.5mm thick
        }
        
        # Apply to the math model
        self.math_model.set_parameters(params)
        
        # Apply to the preview
        self.preview_3d.set_parameters(params)
        
        # Set tool parameters
        tool_params = {
            'diameter': 0.1,  # 0.1mm
            'shape': 'ball',
            'tip_angle': 0    # Not applicable for ball
        }
        self.math_model.set_tool_geometry(tool_params)
        self.preview_3d.set_tool_geometry(tool_params)
        
        # Update status
        self.statusBar().showMessage("Default parameters applied")
    
    @pyqtSlot()
    def apply_parameters(self):
        """Apply current UI parameters to the model and update the 3D preview."""
        try:
            # 1. Collect all current parameters from UI
            current_params = self._collect_current_parameters()

            # 2. Update MathModel with these parameters
            self.math_model.set_parameters(current_params)

            # 3. Get the pattern generating function from MathModel
            pattern_function = self.math_model.get_guilloche_pattern(current_params['pattern_type'])
            if pattern_function is None:
                QMessageBox.warning(self, "Preview Error", f"Could not get pattern function for type: {current_params['pattern_type']}")
                self.statusBar().showMessage(f"Error: Could not get pattern function for {current_params['pattern_type']}")
                return

            # 4. Instantiate ToolpathPlanner and generate 2D XY points
            toolpath_planner = ToolpathPlanner(
                pattern_generator_func=pattern_function,
                base_radius=current_params['base_radius'], # MathModel uses mp.mpf, ToolpathPlanner expects float
                num_points=current_params['num_points'],
                tolerance=current_params['tolerance']
            )
            xy_points = toolpath_planner.generate_xy_points()

            if xy_points is None or len(xy_points) == 0:
                QMessageBox.warning(self, "Preview Error", "ToolpathPlanner failed to generate 2D points for preview.")
                self.statusBar().showMessage("Error: ToolpathPlanner failed to generate 2D points for preview.")
                return
            
            if not isinstance(xy_points, np.ndarray):
                xy_points = np.array(xy_points, dtype=float)
            
            if xy_points.ndim != 2 or xy_points.shape[1] != 2:
                QMessageBox.warning(self, "Preview Error", f"Generated 2D path for preview has incorrect shape: {xy_points.shape}. Expected Nx2.")
                self.statusBar().showMessage("Error: Generated 2D path for preview has incorrect shape.")
                return

            # 5. Update the 3D Preview Widget

            # 5a. Set workpiece and general parameters in Preview3DWidget
            # (Preview3DWidget.set_parameters extracts workpiece_diameter, thickness, z_depth, num_passes)
            self.preview_3d.set_parameters(current_params)

            # 5b. Set tool geometry in Preview3DWidget
            tool_geometry_for_preview = {
                'shape': current_params.get('tool_type', 'ball'),
                'diameter': current_params.get('tool_diameter', 0.1),
                'tip_angle': current_params.get('tool_tip_angle', 0) # Default to 0 if not applicable
            }
            self.preview_3d.set_tool_geometry(tool_geometry_for_preview)

            # 5c. Generate 3D toolpath using DepthMapper
            depth_mapper = DepthMapper()
            try:
                path_3d = depth_mapper.generate_3d_toolpath(
                    xy_points,
                    total_depth=abs(current_params.get('z_depth', 0.05)),
                    num_passes=current_params.get('num_passes', 1),
                    tool_shape=current_params.get('tool_type', 'ball'),
                    tool_diameter=current_params.get('tool_diameter', 0.1),
                    tip_angle=current_params.get('tool_tip_angle', None) # Pass None if not applicable for shape
                )
                if path_3d is None or len(path_3d) == 0:
                    QMessageBox.warning(self, "Preview Error", "DepthMapper failed to generate 3D path for preview.")
                    self.statusBar().showMessage("Error: DepthMapper failed to generate 3D path.")
                    self.preview_3d.set_path_data(None) # Clear previous path
                    return
            except Exception as dm_e:
                QMessageBox.critical(self, "DepthMapper Error", f"Error in DepthMapper: {str(dm_e)}")
                self.statusBar().showMessage(f"Error in DepthMapper: {str(dm_e)}")
                self.preview_3d.set_path_data(None) # Clear previous path
                print(f"DepthMapper Error: {traceback.format_exc()}")
                return

            # 5d. Set the generated 3D path in Preview3DWidget
            # This will trigger update_visualization within Preview3DWidget.
            self.preview_3d.set_path_data(path_3d)

            self.statusBar().showMessage("Parameters applied and preview updated.")

        except Exception as e:
            error_message = f"Error applying parameters for preview:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Preview Error", f"An error occurred: {e}")
            self.statusBar().showMessage("Error applying parameters for preview.")
            print(error_message)
    
    @pyqtSlot()
    def generate_gcode(self):
        """Generate G-code from current parameters and display in output area."""
        # First apply current parameters
        self.apply_parameters() # Restored this call
        
        # Get the current path data from the math model using adaptive generation
        pattern_type = self.pattern_type_combo.currentText()
        max_points_val = self.points_spinbox.value()
        # generate_toolpath_adaptive returns x, y, z_mapped.
        # For current GCodeGenerator.multi_pass_engraving, we only use x, y.
        # The z_depth for engraving will be taken from z_depth_spinbox.
        # True 3D G-code from z_mapped is a future step.
        x, y, _ = self.math_model.generate_toolpath_adaptive(
            pattern_type=pattern_type, 
            max_points=max_points_val
        )
        
        # Get material and tool selections
        material = self.material_combo.currentText()
        tool_name = self.tool_type_combo.currentText()
        num_passes = self.num_passes_spinbox.value()
        
        try:
            # Generate G-code with multiple passes
            z_depth = self.z_depth_spinbox.value()
            gcode = self.gcode_generator.multi_pass_engraving(
                x, y, z_depth, material=material, 
                tool_name=tool_name, num_passes=num_passes
            )
            
            # Display in output area
            self.gcode_output.setText(gcode)
            
            # Enable save button
            self.save_gcode_button.setEnabled(True)
            
            # Update status
            self.statusBar().showMessage(f"G-code generated: {len(gcode.splitlines())} lines")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate G-code: {str(e)}")
            self.statusBar().showMessage("G-code generation failed")
    
    @pyqtSlot()
    def save_gcode(self):
        """Save the generated G-code to a file."""
        if not self.gcode_output.toPlainText():
            QMessageBox.warning(self, "Warning", "No G-code has been generated yet.")
            return
            
        # Get file name from dialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save G-code", "", "G-code Files (*.gcode *.nc);;All Files (*)"
        )
        
        if not file_name:
            return  # User cancelled
            
        try:
            # Save the G-code to file
            with open(file_name, 'w') as f:
                f.write(self.gcode_output.toPlainText())
                
            self.statusBar().showMessage(f"G-code saved to {file_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save G-code: {str(e)}")
            self.statusBar().showMessage("G-code save failed")
    
    @pyqtSlot()
    def reset_preview(self):
        """Reset the 3D preview camera to default position."""
        self.preview_3d.reset_view()
        self.statusBar().showMessage("Preview view reset")
    
    @pyqtSlot()
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(self, "About Digital Rose Engine Simulator",
                          "<p><b>Digital Rose Engine Simulator</b></p>"
                          "<p>Version 0.2</p>"
                          "<p>This application simulates a rose engine lathe for generating guilloché patterns "
                          "and producing G-code for CNC machining.</p>"
                          "<p>Developed with PyQt6 and Python.</p>")

    def _collect_current_parameters(self):
        """Helper function to collect all current parameters from the UI for MathModel and Preview."""
        params = {
            'pattern_type': self.pattern_type_combo.currentText(),
            'cam_amplitude': self.cam_amplitude_spinbox.value(),
            'cam_lobes': self.cam_lobes_spinbox.value(),
            'cam_phase_offset': self.cam_phase_offset_spinbox.value(),
            'base_radius': self.base_radius_spinbox.value(),
            'workpiece_diameter': self.workpiece_diameter_spinbox.value(),
            'workpiece_thickness': self.workpiece_thickness_spinbox.value(),
            'material': self.material_combo.currentText(),
            'tool_type': self.tool_type_combo.currentText(),
            'z_depth': self.z_depth_spinbox.value(), # This is total cut depth
            'num_passes': self.num_passes_spinbox.value(),
            'tolerance': self.tolerance_spinbox.value(),
            'num_points': self.points_spinbox.value(),
            'harmonics': []
        }
        if self.pattern_type_combo.currentText() == 'custom_harmonic':
            # Ensure harmonic_input_rows stores tuples/dicts as expected by logic below
            # Based on _add_harmonic_input_row, it stores dicts: {'amp': QDoubleSpinBox, ...}
            for harmonic_row_widgets in self.harmonic_input_rows:
                params['harmonics'].append({
                    'amplitude': harmonic_row_widgets['amp'].value(),
                    'lobes': harmonic_row_widgets['lobes'].value(),
                    'phase': harmonic_row_widgets['phase'].value()
                })
        return params

    def _collect_gcode_parameters(self):
        """Collects parameters specifically for G-code generation from the UI."""
        coolant_setting = self.coolant_checkbox.currentText()
        coolant_on_command = None
        coolant_off_command = "M9" # Standard coolant off
        if "M7" in coolant_setting: # Mist
            coolant_on_command = "M7"
        elif "M8" in coolant_setting: # Flood
            coolant_on_command = "M8"
        
        total_depth = abs(self.z_depth_spinbox.value())
        num_passes = self.num_passes_spinbox.value()
        if num_passes <= 0: num_passes = 1 # Avoid division by zero
        depth_per_pass = total_depth / num_passes

        return {
            'total_depth_mm': total_depth,
            'depth_per_pass_mm': depth_per_pass,
            'safe_z_mm': self.safe_z_mm_spinbox.value(),
            'material_top_z_mm': 0.0, # Assuming material top is Z0
            'default_feed_rate': self.default_feed_rate_spinbox.value(),
            'plunge_feed_rate': self.plunge_feed_rate_spinbox.value(),
            'spindle_rpm': self.spindle_rpm_spinbox.value(),
            'tool_number': self.tool_number_spinbox.value(),
            'coolant_on_command': coolant_on_command,
            'coolant_off_command': coolant_off_command,
            'pattern_name': self.pattern_type_combo.currentText(),
            'num_passes_for_comment': num_passes 
        }

    @pyqtSlot()
    def on_generate_gcode_clicked(self):
        """Handles the 'Generate G-code' button click."""
        try:
            self.gcode_output_textedit.clear()
            self.gcode_engine.clear_moves() 

            current_params = self._collect_current_parameters()
            gcode_params = self._collect_gcode_parameters()

            # 1. Update MathModel with current parameters
            self.math_model.set_parameters(current_params) # Pass all relevant UI params

            # 2. Get the pattern generating function from MathModel
            # The pattern_type is already in current_params and set in math_model
            pattern_function = self.math_model.get_guilloche_pattern(current_params['pattern_type'])
            if pattern_function is None:
                QMessageBox.warning(self, "G-code Error", f"Could not get pattern function for type: {current_params['pattern_type']}")
                return

            # 3. Instantiate ToolpathPlanner and generate 2D XY points
            # Ensure all necessary parameters for ToolpathPlanner are available in current_params
            # or passed explicitly. ToolpathPlanner might need base_radius, num_points, tolerance.
            toolpath_planner = ToolpathPlanner(
                pattern_generator_func=pattern_function, 
                base_radius=current_params['base_radius'],
                num_points=current_params['num_points'],
                tolerance=current_params['tolerance']
            )
            # The generate_xy_points might need theta_range or other specifics.
            # Assuming default theta_range [0, 2*pi] or handled internally by ToolpathPlanner/MathModel
            xy_points = toolpath_planner.generate_xy_points()

            if xy_points is None or len(xy_points) == 0:
                QMessageBox.warning(self, "G-code Error", "ToolpathPlanner failed to generate 2D points.")
                return
            
            # Ensure xy_points is a NumPy array for DepthMapper
            if not isinstance(xy_points, np.ndarray):
                xy_points = np.array(xy_points, dtype=float)
            
            # For DepthMapper, xy_points should be Nx2 (X, Y)
            if xy_points.ndim != 2 or xy_points.shape[1] != 2:
                QMessageBox.warning(self, "G-code Error", f"Generated 2D path has incorrect shape: {xy_points.shape}. Expected Nx2.")
                return

            if gcode_params['total_depth_mm'] <= 0 or gcode_params['depth_per_pass_mm'] <=0:
                QMessageBox.warning(self, "G-code Error", "Total depth and depth per pass must be greater than zero.")
                return

            depth_mapper = DepthMapper(
                total_depth_mm=gcode_params['total_depth_mm'],
                depth_per_pass_mm=gcode_params['depth_per_pass_mm'],
                safe_z_mm=gcode_params['safe_z_mm'],
                material_top_z_mm=gcode_params['material_top_z_mm'],
                feed_rate_plunge_mm_min=gcode_params['plunge_feed_rate']
            )
            # 4. Generate 3D toolpath using the actual xy_points
            multi_pass_3d_toolpath = depth_mapper.generate_multi_pass_3d_toolpath(xy_points)

            if not multi_pass_3d_toolpath:
                self.gcode_output_textedit.setText("(No toolpath generated - check parameters or path data)")
                return

            engine_params_for_template = {
                'spindle_rpm': gcode_params['spindle_rpm'],
                'default_feed_rate': gcode_params['default_feed_rate'],
                'plunge_feed_rate': gcode_params['plunge_feed_rate'], 
                'coolant_on_command': gcode_params['coolant_on_command'],
                'coolant_off_command': gcode_params['coolant_off_command'],
                'tool_number': gcode_params['tool_number'],
                'pattern_name': gcode_params['pattern_name'],
                'total_depth_mm': gcode_params['total_depth_mm'],
                'num_passes': depth_mapper.num_passes, 
                'safe_z_retract': gcode_params['safe_z_mm'] 
            }
            self.gcode_engine.set_parameters(engine_params_for_template)
            self.gcode_engine.add_comment(f"Pattern: {gcode_params['pattern_name']}")
            self.gcode_engine.add_comment(f"Total Depth: {gcode_params['total_depth_mm']:.3f} mm, Passes: {depth_mapper.num_passes}")
            self.gcode_engine.process_3d_toolpath(multi_pass_3d_toolpath, default_cut_feed=gcode_params['default_feed_rate'])

            generated_gcode = self.gcode_engine.get_gcode()
            self.gcode_output_textedit.setText(generated_gcode)
            self.output_tabs.setCurrentWidget(self.gcode_output_widget) 
            if hasattr(self, 'save_gcode_button') and hasattr(self.save_gcode_button, 'setEnabled'): # Enable save button on main panel if it exists
                self.save_gcode_button.setEnabled(True)
            # Also enable the button under the text edit if it's the one being used
            if hasattr(self, 'gcode_output_widget') and hasattr(self.gcode_output_widget.layout().itemAt(1).widget(), 'setEnabled'):
                self.gcode_output_widget.layout().itemAt(1).widget().setEnabled(True)

        except Exception as e:
            error_message = f"Error generating G-code:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self.gcode_output_textedit.setText(error_message)
            QMessageBox.critical(self, "G-code Generation Error", f"An error occurred: {e}")
            print(error_message) # Also print to console

    @pyqtSlot()
    def on_save_gcode_clicked(self):
        """Handles the 'Save G-code to File...' button click (for button under text area)."""
        current_gcode = self.gcode_output_textedit.toPlainText()
        if not current_gcode.strip() or current_gcode.startswith("Error generating G-code"):
            QMessageBox.warning(self, "Save G-code", "No valid G-code to save. Please generate G-code first.")
            return

        pattern_name = self.pattern_type_combo.currentText().replace(" ", "_").lower()
        default_filename = f"{pattern_name}_pattern.gcode"
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        suggested_dir = os.path.join(project_root, "output", "gcode")
        os.makedirs(suggested_dir, exist_ok=True)
        default_save_path = os.path.join(suggested_dir, default_filename)

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save G-code File",
            default_save_path, 
            "G-code Files (*.gcode *.nc *.tap);;All Files (*)"
        )

        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(current_gcode)
                QMessageBox.information(self, "G-code Saved", f"G-code successfully saved to:\n{filepath}")
                print(f"G-code saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save G-code file: {e}")
                print(f"Error saving G-code to {filepath}: {e}")

        QMessageBox.about(
            self, 
            "About Digital Rose Engine Simulator",
            "<h3>Digital Rose Engine Simulator</h3>"
            "<p>A software tool for simulating rose engine patterns and generating G-code for CNC machines.</p>"
            "<p>Optimized for small-scale guilloche engraving (≤ 5mm).</p>"
            "<p>Version 1.0</p>"
        )

if __name__ == '__main__':
    # This part is for testing this window directly, not used when run from main.py
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
