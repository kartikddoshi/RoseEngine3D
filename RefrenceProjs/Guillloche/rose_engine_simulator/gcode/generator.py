import numpy as np
import math
import os
from datetime import datetime

class GCodeGenerator:
    """Generator for CNC G-code from rose engine patterns.
    
    This generator is specifically optimized for micro-scale guilloche engraving,
    with features for:
    - High precision movements (down to 0.001mm)
    - Tool compensation for micro-engraving tools
    - Feed rate optimization for different materials
    - Safety features to prevent tool breakage
    """
    
    def __init__(self):
        """Initialize the G-code generator with default settings."""
        # Default G-code settings
        self.feed_rate = 100  # mm/min
        self.plunge_rate = 50  # mm/min
        self.safe_z = 1.0  # mm
        self.precision = 4  # decimal places
        self.controller_type = 'GRBL'  # Default controller
        
        # Material-specific settings
        self.material_settings = {
            'brass': {
                'feed_rate': 100,  # mm/min
                'plunge_rate': 30,  # mm/min
                'stepdown': 0.02,  # mm per pass
                'finish_pass': 0.01  # mm
            },
            'silver': {
                'feed_rate': 80,  # mm/min
                'plunge_rate': 20,  # mm/min
                'stepdown': 0.01,  # mm per pass
                'finish_pass': 0.005  # mm
            },
            'aluminum': {
                'feed_rate': 120,  # mm/min
                'plunge_rate': 40,  # mm/min
                'stepdown': 0.03,  # mm per pass
                'finish_pass': 0.01  # mm
            },
            'gold': {
                'feed_rate': 60,  # mm/min
                'plunge_rate': 15,  # mm/min
                'stepdown': 0.01,  # mm per pass
                'finish_pass': 0.005  # mm
            }
        }
        
        # Tool-specific settings
        self.tool_settings = {
            'ball_0.1mm': {
                'diameter': 0.1,  # mm
                'shape': 'ball',
                'stepover': 0.05,  # mm (50% of diameter)
                'max_depth': 0.1   # mm
            },
            'v_bit_30deg': {
                'diameter': 0.1,  # mm at tip
                'shape': 'v-bit',
                'angle': 30,  # degrees
                'stepover': 0.05,  # mm
                'max_depth': 0.2   # mm
            },
            'flat_0.2mm': {
                'diameter': 0.2,  # mm
                'shape': 'flat',
                'stepover': 0.1,  # mm (50% of diameter)
                'max_depth': 0.2   # mm
            }
        }
        
    def configure(self, settings):
        """Configure the G-code generator with user settings.
        
        Args:
            settings (dict): Dictionary of settings for the G-code generator
        """
        # Update general settings
        if 'feed_rate' in settings:
            self.feed_rate = settings['feed_rate']
        if 'plunge_rate' in settings:
            self.plunge_rate = settings['plunge_rate']
        if 'safe_z' in settings:
            self.safe_z = settings['safe_z']
        if 'precision' in settings:
            self.precision = settings['precision']
        if 'controller_type' in settings:
            self.controller_type = settings['controller_type']
    
    def set_material(self, material_name):
        """Set feed rates and other parameters based on the workpiece material.
        
        Args:
            material_name (str): Name of the material ('brass', 'silver', etc.)
        """
        if material_name in self.material_settings:
            settings = self.material_settings[material_name]
            self.feed_rate = settings['feed_rate']
            self.plunge_rate = settings['plunge_rate']
            return True
        return False
    
    def set_tool(self, tool_name):
        """Set tool-specific parameters.
        
        Args:
            tool_name (str): Name of the tool ('ball_0.1mm', 'v_bit_30deg', etc.)
        """
        if tool_name in self.tool_settings:
            return self.tool_settings[tool_name]
        return None
    
    def _format_number(self, number):
        """Format a number to the specified precision.
        
        Args:
            number (float): Number to format
            
        Returns:
            str: Formatted number string
        """
        format_string = f"{{:.{self.precision}f}}"
        return format_string.format(number).rstrip('0').rstrip('.')
    
    def _get_header(self, tool_info=None, material=None):
        """Generate the G-code file header with comments and setup commands.
        
        Args:
            tool_info (dict, optional): Tool information
            material (str, optional): Material name
            
        Returns:
            list: List of G-code lines for the header
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        header = [
            f"; Rose Engine Simulator G-code",
            f"; Generated: {timestamp}",
            f"; Material: {material if material else 'Unknown'}",
        ]
        
        if tool_info:
            header.extend([
                f"; Tool: {tool_info.get('shape', 'Unknown')} {tool_info.get('diameter', 0)}mm",
                f"; Max Depth: {tool_info.get('max_depth', 0)}mm"
            ])
        
        # Add controller-specific initialization
        if self.controller_type == 'GRBL':
            header.extend([
                "G21 ; Set units to millimeters",
                "G90 ; Set absolute positioning",
                f"G0 Z{self.safe_z} ; Move to safe Z height",
                "G0 X0 Y0 ; Move to origin"
            ])
        elif self.controller_type == 'Mach3':
            header.extend([
                "G21 ; Set units to millimeters",
                "G90 ; Set absolute positioning",
                f"G0 Z{self.safe_z} F{self.feed_rate*2} ; Move to safe Z height",
                "G0 X0 Y0 ; Move to origin"
            ])
        
        return header
    
    def _get_footer(self):
        """Generate the G-code file footer with end commands.
        
        Returns:
            list: List of G-code lines for the footer
        """
        footer = [
            f"G0 Z{self.safe_z} ; Move to safe Z height",
            "G0 X0 Y0 ; Return to origin",
            "M5 ; Turn off spindle",
            "M30 ; Program end and rewind"
        ]
        
        return footer
    
    def generate_gcode(self, x, y, z, material='brass', tool_name='ball_0.1mm', filename=None):
        """Generate G-code for the given toolpath.
        
        Args:
            x (np.array): X coordinates
            y (np.array): Y coordinates
            z (np.array): Z coordinates
            material (str): Material name
            tool_name (str): Tool name
            filename (str, optional): Output filename. If None, returns the G-code as a string.
            
        Returns:
            str or bool: G-code string if filename is None, otherwise True if successful
        """
        # Set material-specific parameters
        self.set_material(material)
        
        # Get tool information
        tool_info = self.set_tool(tool_name)
        
        # Generate header
        gcode_lines = self._get_header(tool_info, material)
        
        # Validate the toolpath
        if len(x) != len(y) or len(x) != len(z):
            raise ValueError("Coordinate arrays must have the same length")
        
        # Start at safe height
        gcode_lines.append(f"G0 Z{self.safe_z}")
        
        # Move to starting position
        gcode_lines.append(f"G0 X{self._format_number(x[0])} Y{self._format_number(y[0])}")
        
        # Plunge to starting depth
        gcode_lines.append(f"G1 Z{self._format_number(z[0])} F{self.plunge_rate}")
        
        # Generate the rest of the path
        for i in range(1, len(x)):
            # Calculate movement distance
            dist = math.sqrt((x[i] - x[i-1])**2 + (y[i] - y[i-1])**2)
            
            # For very small movements, we might need to adjust feed rate
            # This prevents the machine from stopping/starting too frequently
            adjusted_feed = self.feed_rate
            if dist < 0.1:  # If movement is less than 0.1mm
                adjusted_feed = min(self.feed_rate, 60)  # Slower feed rate for precision
            
            # For micro-scale engraving, use very small increments (G01 linear interpolation)
            gcode_lines.append(f"G1 X{self._format_number(x[i])} Y{self._format_number(y[i])} " +
                              f"Z{self._format_number(z[i])} F{adjusted_feed}")
            
            # Add a small delay every 100 points to prevent buffer overflow on some controllers
            if i % 100 == 0 and self.controller_type == 'GRBL':
                gcode_lines.append(f"G4 P0.01 ; Small dwell to prevent buffer issues")
        
        # Add footer
        gcode_lines.extend(self._get_footer())
        
        # Write to file or return as string
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(gcode_lines))
            return True
        else:
            return '\n'.join(gcode_lines)
    
    def multi_pass_engraving(self, x, y, z_depth, material='brass', tool_name='ball_0.1mm', 
                             num_passes=None, filename=None):
        """Generate G-code for multi-pass engraving.
        
        For micro-engraving, multiple passes at increasing depths produce better results.
        
        Args:
            x (np.array): X coordinates
            y (np.array): Y coordinates
            z_depth (float): Final depth (negative value)
            material (str): Material name
            tool_name (str): Tool name
            num_passes (int, optional): Number of passes. If None, calculated from material.
            filename (str, optional): Output filename
            
        Returns:
            str or bool: G-code string if filename is None, otherwise True if successful
        """
        # Set material-specific parameters
        self.set_material(material)
        
        # Get tool information
        tool_info = self.set_tool(tool_name)
        
        # Calculate appropriate number of passes if not specified
        if num_passes is None:
            material_settings = self.material_settings.get(material, 
                                                          self.material_settings['brass'])
            stepdown = material_settings['stepdown']
            num_passes = max(2, int(abs(z_depth) / stepdown))
        
        # Generate header
        gcode_lines = self._get_header(tool_info, material)
        
        # Start at safe height
        gcode_lines.append(f"G0 Z{self.safe_z}")
        
        # For each pass
        for pass_num in range(1, num_passes + 1):
            # Calculate depth for this pass
            current_depth = (z_depth * pass_num) / num_passes
            
            # Add a comment to indicate the current pass
            gcode_lines.append(f"; Pass {pass_num}/{num_passes} - Depth: {current_depth}mm")
            
            # Move to starting position
            gcode_lines.append(f"G0 X{self._format_number(x[0])} Y{self._format_number(y[0])}")
            
            # Plunge to current depth
            gcode_lines.append(f"G1 Z{self._format_number(current_depth)} F{self.plunge_rate}")
            
            # Generate the path for this pass
            for i in range(1, len(x)):
                gcode_lines.append(f"G1 X{self._format_number(x[i])} Y{self._format_number(y[i])} " +
                                  f"Z{self._format_number(current_depth)} F{self.feed_rate}")
            
            # Return to safe Z between passes
            gcode_lines.append(f"G0 Z{self.safe_z}")
        
        # Add footer
        gcode_lines.extend(self._get_footer())
        
        # Write to file or return as string
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(gcode_lines))
            return True
        else:
            return '\n'.join(gcode_lines)
    
    def generate_test_pattern(self, diameter=5.0, material='brass', tool_name='ball_0.1mm', filename=None):
        """Generate a simple test pattern of concentric circles for calibration.
        
        Args:
            diameter (float): Diameter of the largest circle in mm
            material (str): Material name
            tool_name (str): Tool name
            filename (str, optional): Output filename
            
        Returns:
            str or bool: G-code string if filename is None, otherwise True if successful
        """
        # Create concentric circles at decreasing depths
        num_circles = 5
        points_per_circle = 200
        
        gcode_lines = self._get_header(self.set_tool(tool_name), material)
        gcode_lines.append(f"G0 Z{self.safe_z}")
        
        for i in range(num_circles):
            radius = (diameter / 2) * (1 - (i / num_circles))
            depth = -0.01 * (i + 1)  # Deeper with each circle
            
            gcode_lines.append(f"; Circle {i+1} - Radius: {radius}mm, Depth: {depth}mm")
            
            # Generate points for this circle
            theta = np.linspace(0, 2*np.pi, points_per_circle)
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            
            # Move to starting point of circle
            gcode_lines.append(f"G0 X{self._format_number(x[0])} Y{self._format_number(y[0])}")
            
            # Plunge to depth
            gcode_lines.append(f"G1 Z{self._format_number(depth)} F{self.plunge_rate}")
            
            # Cut the circle
            for j in range(1, points_per_circle):
                gcode_lines.append(f"G1 X{self._format_number(x[j])} Y{self._format_number(y[j])} F{self.feed_rate}")
            
            # Complete the circle
            gcode_lines.append(f"G1 X{self._format_number(x[0])} Y{self._format_number(y[0])} F{self.feed_rate}")
            
            # Return to safe Z
            gcode_lines.append(f"G0 Z{self.safe_z}")
        
        # Add footer
        gcode_lines.extend(self._get_footer())
        
        # Write to file or return as string
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(gcode_lines))
            return True
        else:
            return '\n'.join(gcode_lines)


if __name__ == "__main__":
    # Example usage
    generator = GCodeGenerator()
    
    # Generate a test pattern
    generator.generate_test_pattern(filename="test_pattern.gcode")
    
    # Generate a simple guilloche pattern
    theta = np.linspace(0, 2*np.pi, 1000)
    radius = 2.0  # 2mm base radius
    amplitude = 0.2  # 0.2mm amplitude
    lobes = 8  # 8-lobed pattern
    
    # Calculate coordinates
    r = radius + amplitude * np.sin(lobes * theta)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.full_like(x, -0.05)  # 0.05mm depth
    
    # Generate G-code with multiple passes
    generator.multi_pass_engraving(x, y, -0.05, material='brass', 
                                   tool_name='ball_0.1mm', num_passes=3,
                                   filename="guilloche_pattern.gcode")
