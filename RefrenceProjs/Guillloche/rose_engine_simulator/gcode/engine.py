import jinja2
import os
from typing import List, Dict, Any, Tuple, Optional

# Assuming DepthMapper output format: List[Tuple[float, float, float, Optional[float], str]]
# where tuple is (X, Y, Z, Feed, Type)
# Types: 'rapid_z_safe', 'plunge', 'cut', 'retract_z_safe'

class GCodeEngine:
    def __init__(self, template_name='default.gcode.j2', template_dir: Optional[str] = None):
        if template_dir is None:
            # Default to 'templates' subdirectory relative to this engine.py file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(base_dir, 'templates')
        
        if not os.path.isdir(template_dir):
            raise FileNotFoundError(f"Jinja2 template directory not found: {template_dir}")
            
        template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
        self.template_env = jinja2.Environment(loader=template_loader, trim_blocks=True, lstrip_blocks=True)
        try:
            self.template = self.template_env.get_template(template_name)
        except jinja2.exceptions.TemplateNotFound:
            raise FileNotFoundError(f"Jinja2 template '{template_name}' not found in {template_dir}")

        self.parameters: Dict[str, Any] = {}
        self.gcode_moves: List[Dict[str, Any]] = [] # Stores moves for the template

    def set_parameters(self, params: Dict[str, Any]):
        """Set parameters for G-code generation (e.g., spindle_rpm, feed_rates)."""
        self.parameters.update(params)
        # Ensure essential parameters have defaults if not provided
        self.parameters.setdefault('spindle_rpm', 1000)
        self.parameters.setdefault('default_feed_rate', 100)
        self.parameters.setdefault('plunge_feed_rate', self.parameters['default_feed_rate'] / 2)
        self.parameters.setdefault('safe_z_retract', 10.0) # Default Z for final retract

    def add_comment(self, text: str):
        """Adds a comment to the G-code moves list."""
        self.gcode_moves.append({'type': 'comment', 'text': text})

    def process_3d_toolpath(
        self,
        toolpath_3d: List[Tuple[float, float, float, Optional[float], str]],
        default_cut_feed: Optional[float] = None
    ):
        """Processes a 3D toolpath from DepthMapper and converts it to G-code move dictionaries."""
        
        if default_cut_feed is None:
            default_cut_feed = self.parameters.get('default_feed_rate')

        last_feed_rate = None

        for x, y, z, feed, move_type_tag in toolpath_3d:
            move_dict: Dict[str, Any] = {'X': x, 'Y': y, 'Z': z}

            if move_type_tag == 'rapid_z_safe' or move_type_tag == 'retract_z_safe':
                move_dict['type'] = 'G0'
                # G0 moves typically don't specify feed, but some controllers might use last G1 feed or a machine default rapid feed.
                # For clarity, we omit F here for G0.
            elif move_type_tag == 'plunge':
                move_dict['type'] = 'G1'
                move_dict['F'] = feed if feed is not None else self.parameters.get('plunge_feed_rate')
            elif move_type_tag == 'cut':
                move_dict['type'] = 'G1'
                # Only specify feed if it's different from the last one or if explicitly provided
                current_feed = feed if feed is not None else default_cut_feed
                if current_feed != last_feed_rate:
                    move_dict['F'] = current_feed
                    last_feed_rate = current_feed
            else:
                self.add_comment(f"WARNING: Unknown move_type_tag: {move_type_tag} at X{x} Y{y} Z{z}")
                continue
            
            self.gcode_moves.append(move_dict)

    def get_gcode(self) -> str:
        """Renders the G-code using the Jinja2 template and collected moves/parameters."""
        if not self.gcode_moves and not self.parameters.get('allow_empty_moves', False):
            # Add a default header/footer even if no moves, unless explicitly allowed
            # This ensures basic structure is present for safety.
            # The template itself handles header/footer blocks.
            pass 

        # Pass parameters and moves to the template
        rendered_gcode = self.template.render(
            params=self.parameters,
            moves=self.gcode_moves
        )
        return rendered_gcode

    def save_gcode(self, filepath: str):
        """Saves the generated G-code to a file."""
        gcode_content = self.get_gcode()
        with open(filepath, 'w') as f:
            f.write(gcode_content)
        print(f"G-code saved to {filepath}")

    def clear_moves(self):
        """Clears the stored G-code moves, useful for generating multiple operations."""
        self.gcode_moves = []

# Example Usage (requires DepthMapper class from core.depth_mapper)
if __name__ == '__main__':
    # This example assumes depth_mapper.py is in a sibling 'core' directory
    import sys
    # Add project root to sys.path to allow imports from core
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from rose_engine_simulator.core.depth_mapper import DepthMapper
    except ImportError:
        print("Could not import DepthMapper. Ensure it's in the correct path (e.g., rose_engine_simulator/core/depth_mapper.py)")
        print("PYTHONPATH:", sys.path)
        exit(1)

    # 1. Setup DepthMapper
    example_xy = [
        [0.0, 0.0],
        [10.0, 0.0],
        [10.0, 10.0],
        [0.0, 10.0],
        [0.0, 0.0]
    ]
    import numpy as np
    xy_np_array = np.array(example_xy, dtype=float)

    depth_mapper_instance = DepthMapper(
        total_depth_mm=0.5,
        depth_per_pass_mm=0.2,
        safe_z_mm=5.0,
        material_top_z_mm=0.0,
        feed_rate_plunge_mm_min=50.0
    )
    multi_pass_toolpath = depth_mapper_instance.generate_multi_pass_3d_toolpath(xy_np_array)

    # 2. Setup GCodeEngine
    engine = GCodeEngine() # Will look for templates/default.gcode.j2
    engine.set_parameters({
        'spindle_rpm': 3000,
        'default_feed_rate': 150.0,
        'plunge_feed_rate': 75.0,
        'coolant_on': True,
        'tool_number': 1,
        'pattern_name': 'Test Square',
        'total_depth_mm': depth_mapper_instance.total_depth_mm,
        'num_passes': depth_mapper_instance.num_passes,
        'safe_z_retract': depth_mapper_instance.safe_z_mm # Use safe_z from depth mapper for final retract
    })

    # 3. Process the toolpath
    engine.add_comment("Starting Test Square Pattern")
    engine.process_3d_toolpath(multi_pass_toolpath)
    engine.add_comment("Finished Test Square Pattern")

    # 4. Get and print G-code
    generated_gcode = engine.get_gcode()
    print("\n--- Generated G-code ---")
    print(generated_gcode)
    print("------------------------")

    # 5. Save G-code
    output_filename = "test_pattern_from_engine.gcode"
    engine.save_gcode(output_filename)
    print(f"Example G-code saved to {output_filename} in current directory ({os.getcwd()})")

    # Test with a non-existent template
    try:
        GCodeEngine(template_name='non_existent.gcode.j2')
    except FileNotFoundError as e:
        print(f"\nSuccessfully caught error for non-existent template: {e}")

    # Test with non-existent template directory
    try:
        GCodeEngine(template_dir='./non_existent_templates_dir')
    except FileNotFoundError as e:
        print(f"\nSuccessfully caught error for non-existent template directory: {e}")
