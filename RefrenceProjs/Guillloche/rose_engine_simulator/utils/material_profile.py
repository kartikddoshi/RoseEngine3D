# Defines material properties and their corresponding machining parameters

DEFAULT_MATERIAL_PROFILES = {
    "brass": {
        "display_name": "Brass",
        "density_g_cm3": 8.5,
        "hardness_brinell": "55-73",
        "machinability_rating_percent": 100, # Free-cutting brass as baseline
        "default_tool_parameters": {
            "end_mill_0.1mm": {
                "spindle_speed_rpm": 20000, # High speed for small tools
                "feed_rate_mm_min": 100,    # Moderate feed
                "depth_of_cut_mm_per_pass": 0.02, # Shallow depth for fine detail
                "coolant_on": False # Often machined dry or with minimal coolant
            },
            "v_bit_30deg_0.1mm_tip": {
                "spindle_speed_rpm": 18000,
                "feed_rate_mm_min": 80,
                "depth_of_cut_mm_per_pass": 0.03,
                "coolant_on": False
            }
        }
    },
    "silver": {
        "display_name": "Silver (Fine, 999)",
        "density_g_cm3": 10.49,
        "hardness_brinell": "25-40", # Annealed
        "machinability_rating_percent": 80, # Gummy, requires sharp tools
        "default_tool_parameters": {
            "end_mill_0.1mm": {
                "spindle_speed_rpm": 15000,
                "feed_rate_mm_min": 60,
                "depth_of_cut_mm_per_pass": 0.015,
                "coolant_on": True # Lubricant recommended
            },
            "v_bit_30deg_0.1mm_tip": {
                "spindle_speed_rpm": 12000,
                "feed_rate_mm_min": 50,
                "depth_of_cut_mm_per_pass": 0.02,
                "coolant_on": True
            }
        }
    },
    "aluminum_6061": {
        "display_name": "Aluminum (6061-T6)",
        "density_g_cm3": 2.70,
        "hardness_brinell": 95,
        "machinability_rating_percent": 120, # Good machinability
        "default_tool_parameters": {
            "end_mill_0.1mm": {
                "spindle_speed_rpm": 25000,
                "feed_rate_mm_min": 150,
                "depth_of_cut_mm_per_pass": 0.025,
                "coolant_on": True # Coolant/lubricant essential
            },
            "v_bit_30deg_0.1mm_tip": {
                "spindle_speed_rpm": 22000,
                "feed_rate_mm_min": 120,
                "depth_of_cut_mm_per_pass": 0.03,
                "coolant_on": True
            }
        }
    },
    "gold_18k_yellow": {
        "display_name": "Gold (18K Yellow)",
        "density_g_cm3": 15.5, # Approx, depends on alloy
        "hardness_brinell": "40-120", # Varies widely with work hardening and alloy
        "machinability_rating_percent": 70, # Can be gummy, similar to silver
        "default_tool_parameters": {
            "end_mill_0.1mm": {
                "spindle_speed_rpm": 16000,
                "feed_rate_mm_min": 70,
                "depth_of_cut_mm_per_pass": 0.01,
                "coolant_on": True # Lubricant recommended
            },
            "v_bit_30deg_0.1mm_tip": {
                "spindle_speed_rpm": 14000,
                "feed_rate_mm_min": 60,
                "depth_of_cut_mm_per_pass": 0.015,
                "coolant_on": True
            }
        }
    }
}

class MaterialProfileManager:
    def __init__(self, profiles=None):
        self.profiles = profiles if profiles else DEFAULT_MATERIAL_PROFILES

    def get_material_names(self):
        return [details["display_name"] for material, details in self.profiles.items()]

    def get_material_key_by_display_name(self, display_name):
        for key, details in self.profiles.items():
            if details["display_name"] == display_name:
                return key
        return None

    def get_profile(self, material_name_key_or_display_name):
        if material_name_key_or_display_name in self.profiles:
            return self.profiles[material_name_key_or_display_name]
        
        key = self.get_material_key_by_display_name(material_name_key_or_display_name)
        if key:
            return self.profiles[key]
        
        print(f"Warning: Material profile '{material_name_key_or_display_name}' not found. Returning default (brass).")
        return self.profiles.get("brass") # Fallback to brass

    def get_tool_parameters(self, material_name, tool_type_key):
        profile = self.get_profile(material_name)
        if profile and "default_tool_parameters" in profile:
            return profile["default_tool_parameters"].get(tool_type_key)
        return None

# Example Usage:
if __name__ == "__main__":
    manager = MaterialProfileManager()
    
    print("Available materials:", manager.get_material_names())
    
    brass_profile = manager.get_profile("Brass")
    print("\nBrass Profile:", brass_profile)
    
    silver_tool_params = manager.get_tool_parameters("Silver (Fine, 999)", "end_mill_0.1mm")
    print("\nSilver tool params for 0.1mm end mill:", silver_tool_params)
    
    gold_tool_params_vbit = manager.get_tool_parameters("gold_18k_yellow", "v_bit_30deg_0.1mm_tip")
    print("\n18K Gold tool params for V-bit:", gold_tool_params_vbit)

    unknown_params = manager.get_tool_parameters("Unobtainium", "laser_cutter_1MW")
    print("\nUnknown Material/Tool:", unknown_params) # Should be None or default

    # Test fallback for unknown material
    unknown_material_profile = manager.get_profile("Titanium Grade 5")
    print("\nProfile for Titanium (should fallback to brass with warning):", unknown_material_profile)

