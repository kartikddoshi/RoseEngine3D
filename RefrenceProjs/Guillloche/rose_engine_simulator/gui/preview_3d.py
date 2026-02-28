import sys
import numpy as np
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSlider, QCheckBox, QComboBox, QApplication)
from PyQt6.QtGui import QSurfaceFormat
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

# (MathModel and PATTERN_MAP imports removed as Preview3DWidget will receive path data directly)

class Preview3DWidget(QWidget):
    """3D preview widget for visualizing guilloche patterns.
    
    This widget uses PyQtGraph's OpenGL capabilities to render a 3D visualization
    of the guilloche pattern, allowing rotation, zooming, and different viewing modes.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # (MathModel instance removed)
        # Parameters to be set by MainWindow
        self.workpiece_params = {} 
        self.tool_params = {}
        self.path_data_3d = None # Will store (x, y, z) points
        
        # Setup the UI layout
        self.init_ui()
        
        # Default display settings
        self.show_toolpath = True
        self.show_workpiece = True
        self.show_axes = True
        # self.current_pattern removed
        self.toolpath_item = None
        self.workpiece_item = None
        
        # Create the initial visualization
        self.update_visualization()
        
    def init_ui(self):
        """Initialize the user interface for the 3D preview."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create the 3D view widget with appropriate format for small-scale precision
        self.view_widget = gl.GLViewWidget()
        
        # Set optimal viewing parameters for small-scale objects
        self.view_widget.setCameraPosition(distance=10, elevation=30, azimuth=45)
        self.view_widget.setMinimumSize(QSize(300, 300))
        
        # Add grid for reference
        grid = gl.GLGridItem()
        grid.setSize(10, 10)
        grid.setSpacing(1, 1)
        self.view_widget.addItem(grid)
        
        # Create axes for reference
        x_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [5, 0, 0]]), color=(1, 0, 0, 1), width=2)
        y_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 5, 0]]), color=(0, 1, 0, 1), width=2)
        z_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 0, 5]]), color=(0, 0, 1, 1), width=2)
        self.view_widget.addItem(x_axis)
        self.view_widget.addItem(y_axis)
        self.view_widget.addItem(z_axis)
        
        # Placeholders for dynamic visualization elements
        self.toolpath_item = None
        self.workpiece_item = None
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Pattern selection UI removed
        
        # View controls
        view_layout = QVBoxLayout()
        view_layout.addWidget(QLabel("View Controls:"))
        
        # Show/hide toolpath
        self.toolpath_checkbox = QCheckBox("Show Toolpath")
        self.toolpath_checkbox.setChecked(True)
        self.toolpath_checkbox.stateChanged.connect(self.on_view_option_changed)
        view_layout.addWidget(self.toolpath_checkbox)
        
        # Show/hide workpiece
        self.workpiece_checkbox = QCheckBox("Show Workpiece")
        self.workpiece_checkbox.setChecked(True)
        self.workpiece_checkbox.stateChanged.connect(self.on_view_option_changed)
        view_layout.addWidget(self.workpiece_checkbox)
        
        # Show/hide axes
        self.axes_checkbox = QCheckBox("Show Axes")
        self.axes_checkbox.setChecked(True)
        self.axes_checkbox.stateChanged.connect(self.on_view_option_changed)
        view_layout.addWidget(self.axes_checkbox)
        
        # Simulation detail slider UI removed
        
        # Arrange the control layouts
        # controls_layout.addLayout(pattern_layout) # Removed
        controls_layout.addLayout(view_layout)
        # controls_layout.addLayout(detail_layout) # Removed
        
        # Add widgets to main layout
        main_layout.addWidget(self.view_widget, stretch=4)
        main_layout.addLayout(controls_layout, stretch=1)
        
        # Set layout
        self.setLayout(main_layout)
        
    def set_parameters(self, params):
        """Set the workpiece and other relevant parameters for visualization.
        
        Args:
            params (dict): Parameters dictionary, expected to contain workpiece_diameter, 
                           workpiece_thickness, z_depth, num_passes etc.
        """
        # Store relevant parameters for workpiece and context
        self.workpiece_params = {
            'diameter': params.get('workpiece_diameter', 5.0), # Default if not provided
            'thickness': params.get('workpiece_thickness', 0.5),
            'z_depth': params.get('z_depth', -0.05), # Total cut depth
            'num_passes': params.get('num_passes', 1)
        }
        # self.math_model.set_parameters(params) # Removed
        # self.update_visualization() # Call will be made by MainWindow after setting path data
        
    def set_tool_geometry(self, tool_params):
        """Set the tool geometry parameters.
        
        Args:
            tool_params (dict): Tool parameters (e.g., type, diameter)
        """
        self.tool_params = tool_params.copy() # Store a copy
        # self.math_model.set_tool_geometry(tool_params) # Removed
        # self.update_visualization() # Call will be made by MainWindow after setting path data
        
    def set_path_data(self, path_data_3d):
        """Set the 3D toolpath data for visualization.
        
        Args:
            path_data_3d (np.ndarray or None): Nx3 array of (x, y, z) points, or None to clear.
        """
        self.path_data_3d = path_data_3d
        self.update_visualization() # Now update visualization when new path data is set
        
    def update_visualization(self):
        """Update the 3D visualization based on current path data and parameters."""
        # Remove previous toolpath if it exists and is in the widget
        if self.toolpath_item is not None and self.toolpath_item in self.view_widget.items:
            self.view_widget.removeItem(self.toolpath_item)
        self.toolpath_item = None # Always clear the reference
            
        # Create new toolpath if needed
        if self.show_toolpath and self.path_data_3d is not None and self.path_data_3d.shape[0] > 0:
            # self.path_data_3d is expected to be an Nx3 numpy array (x, y, z)
            points = self.path_data_3d
            
            # Create path with vibrant color
            self.toolpath_item = gl.GLLinePlotItem(
                pos=points, 
                color=(1, 0.5, 0, 1),  # Orange
                width=2,               # Line width
                antialias=True         # Smooth lines
            )
            self.view_widget.addItem(self.toolpath_item)
            
        # Update the workpiece visualization
        self.update_workpiece()
            
    def update_workpiece(self):
        """Update the workpiece visualization using a simple cylinder."""
        # Remove previous workpiece if it exists and is in the widget
        if self.workpiece_item is not None and self.workpiece_item in self.view_widget.items:
            self.view_widget.removeItem(self.workpiece_item)
        self.workpiece_item = None # Always clear the reference
            
        # Create new workpiece if needed
        if self.show_workpiece and self.workpiece_params:
            diameter = self.workpiece_params.get('diameter', 5.0)
            thickness = self.workpiece_params.get('thickness', 0.5)
            radius = diameter / 2.0
            
            # Create cylinder mesh data (rows, cols, radius, length)
            # The cylinder is created along the Z-axis by default.
            # We want it to extend from z=0 to z=-thickness.
            md = gl.MeshData.cylinder(rows=10, cols=20, radius=[radius, radius], length=thickness)
            
            # Translate the mesh so its top is at z=0 and it extends downwards
            # The default cylinder is centered at (0,0,0) and extends from -length/2 to length/2.
            # We need to shift it down by thickness/2.
            translation_matrix = pg.Transform3D()
            translation_matrix.translate(0, 0, -thickness / 2.0)
            md.transform(translation_matrix)

            self.workpiece_item = gl.GLMeshItem(
                meshdata=md,
                smooth=True,
                color=(0.7, 0.7, 0.7, 0.5),  # Light gray, semi-transparent
                shader='shaded',
                glOptions='translucent'
            )
            self.view_widget.addItem(self.workpiece_item)
    
        
    def on_view_option_changed(self):
        """Handle view options (checkboxes) changes."""
        self.show_toolpath = self.toolpath_checkbox.isChecked()
        self.show_workpiece = self.workpiece_checkbox.isChecked()
        self.show_axes = self.axes_checkbox.isChecked()
        
        # Update visualization
        self.update_visualization()
        
        
    def reset_view(self):
        """Reset the camera to the default position."""
        self.view_widget.setCameraPosition(distance=10, elevation=30, azimuth=45)


if __name__ == "__main__":
    # Set up high-DPI scaling
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Example usage
    app = QApplication(sys.argv)
    
    # Create widget
    preview = Preview3DWidget()
    
    # Set example parameters
    params = {
        'cam_amplitude': 0.5,      # 0.5mm amplitude
        'cam_lobes': 8,            # 8 lobes
        'cam_phase_offset': 0,     # No phase offset
        'base_radius': 2.0,        # 2mm radius
        'z_depth': -0.05,          # 0.05mm depth
        'workpiece_diameter': 5.0, # 5mm diameter workpiece
        'workpiece_thickness': 0.5 # 0.5mm thick
    }
    preview.set_parameters(params)
    
    # Set example tool
    tool_params = {
        'diameter': 0.1,  # 0.1mm
        'shape': 'ball',
        'tip_angle': 0    # Not applicable for ball
    }
    preview.set_tool_geometry(tool_params)
    
    # Show widget
    preview.setWindowTitle("Guilloche 3D Preview")
    preview.resize(800, 600)
    preview.show()
    
    sys.exit(app.exec())
