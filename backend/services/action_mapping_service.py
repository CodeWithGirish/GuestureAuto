import os
import json

class ActionMappingService:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'Data', 'action_mappings.json')
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def get_mappings(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def save_mapping(self, mapping_data):
        try:
            mappings = self.get_mappings()
            
            gesture_name = mapping_data.get('gesture_name')
            target_app = mapping_data.get('target_app', 'Global')
            
            # UPDATED: Only overwrite if BOTH the gesture and the target app are exactly the same
            mappings = [m for m in mappings if not (m.get('gesture_name') == gesture_name and m.get('target_app', 'Global') == target_app)]
            
            mappings.append(mapping_data)
            
            with open(self.data_file, 'w') as f:
                json.dump(mappings, f, indent=4)
                
            return {"status": "success", "message": "Mapping saved successfully!"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to save mapping: {str(e)}"}

    # UPDATED: Added target_app parameter to ensure we only delete the specific mapping
    def delete_mapping(self, gesture_name, target_app="Global"):
        try:
            mappings = self.get_mappings()
            
            # Filter out ONLY the specific mapping for that gesture and app
            mappings = [m for m in mappings if not (m.get('gesture_name') == gesture_name and m.get('target_app', 'Global') == target_app)]
            
            with open(self.data_file, 'w') as f:
                json.dump(mappings, f, indent=4)
                
            return {"status": "success", "message": f"Mapping for {gesture_name} on {target_app} deleted."}
        except Exception as e:
            return {"status": "error", "message": str(e)}