import numpy as np
import mpmath as mp
from scipy import interpolate
import trimesh
from scipy.spatial import Delaunay

# NEW IMPORTS for modular pattern + adaptive toolpath
from .pattern_generator import create_pattern
from .toolpath_planner import generate_xy

# Set precision for mpmath
mp.mp.dps = 50  # Set to 50 decimal places for high precision calculations

class MathModel:
    def __init__(self):
        """Initializes the mathematical model for the rose engine simulator.
        
        This enhanced model supports micro-scale guilloche patterns with high precision
        and complex pattern overlays typical in watchmaking.
        """
        self.parameters = {}
        self.tool_geometry = None
        self.material_properties = None
        self.tolerance = 0.001  # Default tolerance in mm (1 micron)
        self.workpiece_bounds = (5, 5, 0.5)  # Default size: 5mm x 5mm x 0.5mm
        self.path_data = None  # Store computed path data
        
    def set_parameters(self, params):
        """Sets the simulation parameters.

        Args:
            params (dict): A dictionary of parameters including cam, spindle, tool settings.
        """
        self.parameters = params
        
        # Update derived parameters
        if 'spindle_rpm' in params:
            self.parameters['angular_velocity'] = 2 * np.pi * params['spindle_rpm'] / 60  # rad/s
            
        # Update tolerance if provided
        if 'tolerance' in params:
            self.tolerance = params['tolerance']
            
        # Update workpiece dimensions if provided
        if 'workpiece_diameter' in params:
            diameter = params['workpiece_diameter']
            thickness = params.get('workpiece_thickness', 0.5)
            self.workpiece_bounds = (diameter, diameter, thickness)
        elif 'workpiece_width' in params and 'workpiece_height' in params:
            width = params['workpiece_width']
            height = params['workpiece_height']
            thickness = params.get('workpiece_thickness', 0.5)
            self.workpiece_bounds = (width, height, thickness)
            
    def set_tool_geometry(self, tool_params):
        """Sets the tool geometry parameters.
        
        Args:
            tool_params (dict): Tool parameters including diameter, tip angle, etc.
        """
        self.tool_geometry = tool_params
        
    def set_material_properties(self, material_params):
        """Sets the material properties affecting machining parameters.
        
        Args:
            material_params (dict): Material parameters including hardness, feed rates, etc.
        """
        self.material_properties = material_params
    
    def get_guilloche_pattern(self, pattern_type='standard'):
        """Returns a function that generates a specific guilloche pattern using mpmath for precision.
        
        Args:
            pattern_type (str): The type of guilloche pattern to generate.
                Options: 'standard', 'custom_harmonic', 'barleycorn', 'basketweave', 'sunburst', 'moiré', 'simple_sine', 'cosine', 'epitrochoid', 'hypotrochoid'
                
        Returns:
            function: A function that takes theta (numpy array or mpmath scalar) 
                      and generates radial displacement (numpy array of mpf or mpf scalar).
        """

        if pattern_type == 'standard':
            # Standard single sine wave rose pattern, using mpmath
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('cam_amplitude', '0.5'))
                n_lobes = mp.mpf(self.parameters.get('cam_lobes', '6'))
                phi = mp.mpf(self.parameters.get('cam_phase_offset', '0'))
                if isinstance(theta_input, np.ndarray):
                    result = np.empty_like(theta_input, dtype=object)
                    for i, theta_val in enumerate(theta_input):
                        result[i] = A * mp.sin(n_lobes * mp.mpf(theta_val) + phi)
                    return result
                else:
                    return A * mp.sin(n_lobes * mp.mpf(theta_input) + phi)

        elif pattern_type == 'custom_harmonic':
            # Pattern defined by a sum of multiple harmonics for complex rosette profiles.
            harmonics_definition = self.parameters.get('harmonics_definition', None)
            
            if harmonics_definition and isinstance(harmonics_definition, list) and len(harmonics_definition) > 0:
                def pattern_func(theta_input):
                    if isinstance(theta_input, np.ndarray):
                        total_displacement = np.array([mp.mpf(0)] * len(theta_input), dtype=object)
                        for i, th_val in enumerate(theta_input):
                            th_mp_scalar = mp.mpf(th_val)  # Convert current theta element to mpf
                            current_sum_for_th_val = mp.mpf(0)
                            for harmonic_params in harmonics_definition:
                                A = mp.mpf(harmonic_params.get('amplitude', '0'))
                                n_lobes = mp.mpf(harmonic_params.get('lobes', '1'))
                                phi = mp.mpf(harmonic_params.get('phase', '0'))
                                term = A * mp.sin(n_lobes * th_mp_scalar + phi)
                                current_sum_for_th_val += term
                            total_displacement[i] = current_sum_for_th_val
                    else:  # scalar theta_input
                        total_displacement = mp.mpf(0)
                        # Ensure theta_input is mpf, even if it's a Python float or int
                        th_mp = mp.mpf(theta_input)
                        for harmonic_params in harmonics_definition:
                            A = mp.mpf(harmonic_params.get('amplitude', '0'))
                            n_lobes = mp.mpf(harmonic_params.get('lobes', '1'))
                            phi = mp.mpf(harmonic_params.get('phase', '0'))
                            total_displacement += A * mp.sin(n_lobes * th_mp + phi)
                    return total_displacement
            else:
                # Fallback for 'custom_harmonic' if definition is invalid/missing: standard sine wave
                def pattern_func(theta_input):
                    A = mp.mpf(self.parameters.get('cam_amplitude', '0.5'))
                    n_lobes = mp.mpf(self.parameters.get('cam_lobes', '6'))
                    phi = mp.mpf(self.parameters.get('cam_phase_offset', '0'))
                    return A * mp.sin(n_lobes * theta_input + phi)
            
        elif pattern_type == 'barleycorn':
            # Barleycorn pattern using mpmath
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('cam_amplitude', '0.3'))
                n1 = mp.mpf(self.parameters.get('primary_lobes', '8'))
                n2 = mp.mpf(self.parameters.get('secondary_lobes', '16'))
                phi1 = mp.mpf(self.parameters.get('primary_phase', '0'))
                phi2 = mp.mpf(self.parameters.get('secondary_phase', str(mp.pi/4))) # Use mp.pi
                term1 = mp.sin(n1 * theta_input + phi1)
                term2 = mp.mpf('0.5') * mp.sin(n2 * theta_input + phi2)
                return A * (term1 + term2)
        
        elif pattern_type == 'basketweave':
            # Basketweave pattern using mpmath
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('cam_amplitude', '0.4'))
                n1 = mp.mpf(self.parameters.get('primary_lobes', '4'))
                n2 = mp.mpf(self.parameters.get('secondary_lobes', '8'))
                return A * (mp.sin(n1 * theta_input) * mp.cos(n2 * theta_input))
        
        elif pattern_type == 'sunburst':
            # Sunburst pattern using mpmath
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('cam_amplitude', '0.5'))
                n_rays = mp.mpf(self.parameters.get('rays', '24'))
                modulation = mp.mpf(self.parameters.get('ray_modulation', '0.2'))
                
                cos_term = mp.cos(n_rays * theta_input)
                if isinstance(cos_term, np.ndarray):
                    # Element-wise power for numpy array of mpf objects
                    powered_cos_term = np.array([val**10 for val in cos_term], dtype=object)
                else: # scalar mpf
                    powered_cos_term = cos_term**10
                return A * (mp.mpf('1') - modulation + modulation * powered_cos_term)

        elif pattern_type == 'moiré':
            # Moiré pattern using mpmath
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('cam_amplitude', '0.4'))
                n1 = mp.mpf(self.parameters.get('primary_lobes', '20'))
                n2 = mp.mpf(self.parameters.get('secondary_lobes', '21'))
                return A * (mp.sin(n1 * theta_input) * mp.sin(n2 * theta_input))
        
        elif pattern_type == 'simple_sine':
            # Sine wave pattern
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('A_sin', '1'))  # Amplitude
                f = mp.mpf(self.parameters.get('f_sin', '1'))  # Frequency
                phi = mp.mpf(self.parameters.get('phi_sin', '0'))  # Phase
                if isinstance(theta_input, np.ndarray):
                    result = np.empty_like(theta_input, dtype=object)
                    for i, theta_val in enumerate(theta_input):
                        result[i] = A * mp.sin(f * mp.mpf(theta_val) + phi)
                    return result
                else:
                    return A * mp.sin(f * mp.mpf(theta_input) + phi)

        elif pattern_type == 'cosine':
            # Cosine wave pattern
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('A_cos', '1'))  # Amplitude
                f = mp.mpf(self.parameters.get('f_cos', '1'))  # Frequency
                phi = mp.mpf(self.parameters.get('phi_cos', '0'))  # Phase
                if isinstance(theta_input, np.ndarray):
                    result = np.empty_like(theta_input, dtype=object)
                    for i, theta_val in enumerate(theta_input):
                        result[i] = A * mp.cos(f * mp.mpf(theta_val) + phi)
                    return result
                else:
                    return A * mp.cos(f * mp.mpf(theta_input) + phi)

        elif pattern_type == 'epitrochoid':
            # Epitrochoid pattern
            def pattern_func(theta_input):
                R_epi = mp.mpf(self.parameters.get('R_epi', '5'))  # Radius of fixed circle
                r_epi = mp.mpf(self.parameters.get('r_epi', '1'))  # Radius of rolling circle
                d_epi = mp.mpf(self.parameters.get('d_epi', '0.8'))  # Distance from center of rolling circle
                if isinstance(theta_input, np.ndarray):
                    result = np.empty_like(theta_input, dtype=object)
                    for i, theta_val in enumerate(theta_input):
                        theta_mp = mp.mpf(theta_val)
                        x = (R_epi + r_epi) * mp.cos(theta_mp) - d_epi * mp.cos(((R_epi + r_epi) / r_epi) * theta_mp)
                        y = (R_epi + r_epi) * mp.sin(theta_mp) - d_epi * mp.sin(((R_epi + r_epi) / r_epi) * theta_mp)
                        result[i] = mp.sqrt(x**2 + y**2) # Return radius for polar plot
                    return result
                else:
                    theta_mp = mp.mpf(theta_input)
                    x = (R_epi + r_epi) * mp.cos(theta_mp) - d_epi * mp.cos(((R_epi + r_epi) / r_epi) * theta_mp)
                    y = (R_epi + r_epi) * mp.sin(theta_mp) - d_epi * mp.sin(((R_epi + r_epi) / r_epi) * theta_mp)
                    return mp.sqrt(x**2 + y**2) # Return radius for polar plot

        elif pattern_type == 'hypotrochoid':
            # Hypotrochoid pattern
            def pattern_func(theta_input):
                R_hypo = mp.mpf(self.parameters.get('R_hypo', '5'))  # Radius of fixed circle
                r_hypo = mp.mpf(self.parameters.get('r_hypo', '3'))  # Radius of rolling circle
                d_hypo = mp.mpf(self.parameters.get('d_hypo', '1.3'))  # Distance from center of rolling circle
                if isinstance(theta_input, np.ndarray):
                    result = np.empty_like(theta_input, dtype=object)
                    for i, theta_val in enumerate(theta_input):
                        theta_mp = mp.mpf(theta_val)
                        x = (R_hypo - r_hypo) * mp.cos(theta_mp) + d_hypo * mp.cos(((R_hypo - r_hypo) / r_hypo) * theta_mp)
                        y = (R_hypo - r_hypo) * mp.sin(theta_mp) - d_hypo * mp.sin(((R_hypo - r_hypo) / r_hypo) * theta_mp)
                        result[i] = mp.sqrt(x**2 + y**2) # Return radius for polar plot
                    return result
                else:
                    theta_mp = mp.mpf(theta_input)
                    x = (R_hypo - r_hypo) * mp.cos(theta_mp) + d_hypo * mp.cos(((R_hypo - r_hypo) / r_hypo) * theta_mp)
                    y = (R_hypo - r_hypo) * mp.sin(theta_mp) - d_hypo * mp.sin(((R_hypo - r_hypo) / r_hypo) * theta_mp)
                    return mp.sqrt(x**2 + y**2) # Return radius for polar plot
        
        else:  # Default fallback if pattern_type is unknown
            # Defaults to standard single sine wave pattern
            def pattern_func(theta_input):
                A = mp.mpf(self.parameters.get('cam_amplitude', '0.5'))
                n_lobes = mp.mpf(self.parameters.get('cam_lobes', '6'))
                phi = mp.mpf(self.parameters.get('cam_phase_offset', '0'))
                return A * mp.sin(n_lobes * theta_input + phi)
        
        return pattern_func
    
    def apply_tool_compensation(self, x, y, z):
        """Apply tool geometry compensation to the path.
        
        For micro-engraving, tool shape and dimensions significantly affect the final result.
        
        Args:
            x, y, z (np.array): Original toolpath coordinates
            
        Returns:
            tuple: (x_comp, y_comp, z_comp) compensated toolpath coordinates
        """
        if self.tool_geometry is None:
            return x, y, z
            
        # Extract tool parameters
        tool_diameter = self.tool_geometry.get('diameter', 0.1)  # Default 0.1mm for micro-engraving
        tool_shape = self.tool_geometry.get('shape', 'ball')
        tip_angle = self.tool_geometry.get('tip_angle', 30)  # Degrees
        
        # Apply compensation based on tool geometry
        if tool_shape == 'ball':
            # Ball nose compensation (simplistic model)
            # For a ball nose tool, the effective cutting radius varies with depth
            z_comp = z.copy()
            r_effective = tool_diameter / 2
            
            # Calculate the effective radius at each point
            # No compensation needed for x,y with ball nose, just z-depth
            return x, y, z_comp
            
        elif tool_shape == 'v-bit':
            # V-bit compensation
            # For a v-bit, the effective cutting width varies with depth
            angle_rad = np.radians(tip_angle)
            # Calculate effective cutting width at given depth
            width_at_depth = 2 * (z * np.tan(angle_rad/2))
            
            # Complex compensation would go here
            # For now, return original coordinates
            return x, y, z
        
        else:
            # Default: no compensation
            return x, y, z
    
    def generate_toolpath_3d(self, pattern_type='standard', num_points=10000):
        """Generates a 3D toolpath for the guilloche pattern.
        
        Args:
            pattern_type (str): Type of guilloche pattern
            num_points (int): Number of points to generate
            
        Returns:
            tuple: (x, y, z) arrays representing the 3D toolpath
        """
        # Get workpiece dimensions
        bound_w, bound_h, bound_t = self.workpiece_bounds

        try:
            # Step 1: Convert to standard Python float. This will fail for non-numeric strings.
            float_w = float(bound_w)
            float_h = float(bound_h)
            # Step 2: Convert float to mp.mpf
            width_mp = mp.mpf(float_w)
            height_mp = mp.mpf(float_h)
            # thickness_mp = mp.mpf(float(bound_t)) # Keep for consistency if thickness is used later in this form
        except (ValueError, TypeError) as e:
            print(f"Warning: Workpiece dimensions {self.workpiece_bounds} could not be converted to float then mpf. Error: {e}. Using default values (5.0, 5.0).")
            width_mp = mp.mpf('5.0')
            height_mp = mp.mpf('5.0')
            # Attempt to preserve original thickness if possible, otherwise default
            try:
                current_thickness_val = self.workpiece_bounds[2]
                default_t_mp = mp.mpf(str(current_thickness_val)) 
            except:
                default_t_mp = mp.mpf('0.5')
            self.workpiece_bounds = (width_mp, height_mp, default_t_mp) # Store mpf objects back

        # Calculate center point and max radius using the mpf versions
        center_x = width_mp / mp.mpf('2') # Also ensure divisor is mpf for consistency
        center_y = height_mp / mp.mpf('2')
        max_radius = min(width_mp, height_mp) / mp.mpf('2') # Use mpf types and mpf divisor
        
        # Generate parameter space
        if self.parameters.get('full_rotation', True):
            # Full 360° rotation
            theta = np.linspace(0, 2 * np.pi, num_points)
        else:
            # Partial rotation
            start_angle = self.parameters.get('start_angle', 0)
            end_angle = self.parameters.get('end_angle', 2 * np.pi)
            theta = np.linspace(start_angle, end_angle, num_points)
        
        # Get the pattern function
        pattern_func = self.get_guilloche_pattern(pattern_type)
        
        # Calculate base radius (without pattern)
        base_radius_param = self.parameters.get('base_radius', max_radius * mp.mpf('0.7'))
        try:
            base_radius = mp.mpf(str(base_radius_param)) # Convert to mpf, ensuring it's treated as a number
        except (ValueError, TypeError):
            print(f"Warning: Invalid base_radius '{base_radius_param}'. Using default 0.7 * max_radius.")
            base_radius = max_radius * mp.mpf('0.7')
        
        # Calculate radial displacement from pattern
        radial_disp = pattern_func(theta)
        
        # Calculate the actual radius at each point
        print(f"DEBUG: (Before loop) base_radius type: {type(base_radius)}, value: {base_radius}")
        print(f"DEBUG: (Before loop) radial_disp type: {type(radial_disp)}") # Value can be very long
        if isinstance(radial_disp, np.ndarray) and len(radial_disp) > 0:
            print(f"DEBUG: (Before loop) radial_disp[0] type: {type(radial_disp[0])}, value: {radial_disp[0]}")

        if isinstance(radial_disp, np.ndarray):
            radius_list = []
            for i, disp_val in enumerate(radial_disp):
                try:
                    if not isinstance(disp_val, mp.mpf):
                        print(f"ERROR: Element radial_disp[{i}] is not mpf. Type: {type(disp_val)}, Value: {disp_val}")
                        raise TypeError(f"Element radial_disp[{i}] (type {type(disp_val)}) is not an mpf object.")
                    
                    # Perform the addition
                    result_val = base_radius + disp_val
                    radius_list.append(result_val)

                except TypeError as te:
                    print(f"CRITICAL_ERROR: TypeError during element-wise addition for radial_disp[{i}]. Error: {te}")
                    print(f"    DEBUG_INFO: base_radius type: {type(base_radius)}, value: {base_radius}")
                    print(f"    DEBUG_INFO: disp_val    type: {type(disp_val)}, value: {disp_val}")
                    raise # Re-raise the caught TypeError to halt execution and see full traceback
                except Exception as e_add:
                    print(f"CRITICAL_ERROR: Other error during element-wise addition for radial_disp[{i}]. Error: {e_add}")
                    print(f"    DEBUG_INFO: base_radius type: {type(base_radius)}, value: {base_radius}")
                    print(f"    DEBUG_INFO: disp_val    type: {type(disp_val)}, value: {disp_val}")
                    raise # Re-raise other exceptions
            radius = np.array(radius_list, dtype=object)
        elif isinstance(radial_disp, mp.mpf): # If radial_disp is a scalar mpf
            radius = base_radius + radial_disp
        else:
            print(f"CRITICAL_ERROR: radial_disp is of unexpected type: {type(radial_disp)}, value: {radial_disp}")
            raise TypeError(f"radial_disp (type {type(radial_disp)}) is neither np.ndarray nor mpf.")
        
        # Convert to Cartesian coordinates
        x = center_x + radius * np.cos(theta)
        y = center_y + radius * np.sin(theta)
        
        # Calculate z values (depth of cut)
        z_depth = self.parameters.get('z_depth', -0.05)  # Default 0.05mm depth
        z = np.full_like(x, z_depth)
        
        # Apply tool compensation if needed
        x, y, z = self.apply_tool_compensation(x, y, z)
        
        # Store the path data for later use
        self.path_data = {
            'x': x, 'y': y, 'z': z, 
            'theta': theta, 
            'pattern_type': pattern_type
        }
        
        return x, y, z
    
    # ------------------------------------------------------------------
    # NEW EXPERIMENTAL ADAPTIVE TOOLPATH
    # ------------------------------------------------------------------
    def generate_toolpath_adaptive(self, pattern_type: str = 'standard', *, max_points: int = 20000):
        """Generate XY-Z arrays using the new composable pattern system with
        adaptive angular sampling.  This does *not* rely on the legacy
        mpmath-heavy loop in :py:meth:`generate_toolpath_3d` and is better suited
        to very dense, complex patterns.
        """
        # Centre & radius information
        bound_w, bound_h, _ = self.workpiece_bounds
        # Use float for Cartesian arrays to avoid object dtype inflation
        center_x = float(bound_w) / 2.0
        center_y = float(bound_h) / 2.0

        # Create pattern instance from factory
        pattern = create_pattern(pattern_type, self.parameters)

        # Adaptive sampling in XY plane (polar → Cartesian)
        x_rel, y_rel = generate_xy(pattern, tol=self.tolerance, max_points=max_points)

        # Shift to workpiece centre
        x = center_x + x_rel
        y = center_y + y_rel

        # Depth mapping – richer Z modulation than constant depth
        radial_vals = np.sqrt(x_rel ** 2 + y_rel ** 2)
        z = map_depth(radial_vals, self.parameters.get('z_depth', -0.05))

        # Tool compensation (reuse existing routine)
        x, y, z = self.apply_tool_compensation(x, y, z)

        # Store for later use
        self.path_data = {'x': x, 'y': y, 'z': z, 'adaptive': True, 'pattern_type': pattern_type}
        return x, y, z
    
    def create_mesh_model(self):
        """Creates a 3D mesh model of the workpiece with the guilloche pattern.
        
        This is useful for visualization and simulation of the final result.
        
        Returns:
            trimesh.Trimesh: A 3D mesh model of the workpiece with the pattern
        """
        if self.path_data is None:
            # Generate path data if not already available
            self.generate_toolpath_3d()
            
        # Get workpiece dimensions
        width, height, thickness = self.workpiece_bounds
        
        # Create a base mesh (rectangular plate)
        vertices = np.array([
            [0, 0, 0],  # Bottom face
            [width, 0, 0],
            [width, height, 0],
            [0, height, 0],
            [0, 0, thickness],  # Top face
            [width, 0, thickness],
            [width, height, thickness],
            [0, height, thickness]
        ])
        
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # Bottom face
            [4, 5, 6], [4, 6, 7],  # Top face
            [0, 1, 5], [0, 5, 4],  # Front face
            [1, 2, 6], [1, 6, 5],  # Right face
            [2, 3, 7], [2, 7, 6],  # Back face
            [3, 0, 4], [3, 4, 7]   # Left face
        ])
        
        # Create the base mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Apply the guilloche pattern to the mesh
        # This is a simplified approach - actual mesh modification would be more complex
        # For now we'll just return the base mesh
        return mesh
    
    def generate_path(self, t_values):
        """Generates the tool path based on current parameters and time values.
        
        Legacy method for compatibility with existing code.
        
        Args:
            t_values (np.array): Array of time values for simulation.

        Returns:
            tuple: (x_coords, y_coords) representing the tool path.
        """
        # Get parameters with proper defaults for small-scale work
        A = self.parameters.get('cam_amplitude', 0.5)  # Default 0.5mm amplitude
        n = self.parameters.get('cam_lobes', 6)       # Default 6 lobes
        phi = self.parameters.get('cam_phase_offset', 0)  # Default phase offset
        R0 = self.parameters.get('base_radius', 2.0)  # Default 2mm radius
        
        # Use constant angular velocity instead of time-based approach
        theta = t_values
        
        # Cam profile (e.g., sine wave for radial displacement)
        cam_driven_radial_motion = A * np.sin(n * theta + phi)
        
        effective_radius = R0 + cam_driven_radial_motion
        
        # Calculate coordinates
        x_coords = effective_radius * np.cos(theta)
        y_coords = effective_radius * np.sin(theta)
        
        return x_coords, y_coords

if __name__ == '__main__':
    # Example Usage
    model = MathModel()
    params = {
        'cam_amplitude': 5,      # mm
        'cam_lobes': 6,          # Number of lobes
        'cam_phase_offset': np.pi / 4, # radians
        'spindle_rpm': 10,       # RPM
        'tool_radial_offset': 20 # mm, base distance of tool from center
    }
    model.set_parameters(params)
    
    # Simulate for one full rotation
    time_for_one_rotation = 60 / params['spindle_rpm']
    t = np.linspace(0, time_for_one_rotation, 1000) # 1000 points for one rotation
    
    x, y = model.generate_path(t)
    
    # Basic plot for verification (requires matplotlib)
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6,6))
        plt.plot(x, y)
        plt.title('Simulated Rose Engine Pattern (Simple Model)')
        plt.xlabel('X (mm)')
        plt.ylabel('Y (mm)')
        plt.axis('equal')
        plt.grid(True)
        plt.show()
    except ImportError:
        print("Matplotlib not installed. Skipping plot.")
        print("Generated path points (first 5):")
        for i in range(min(5, len(x))):
            print(f"({x[i]:.4f}, {y[i]:.4f})")
