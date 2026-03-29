import os
import json
from backend.services.app_manager import AppManager

class IntegrationAPI:
    def __init__(self):
        self.app_manager = AppManager()
        
        self.data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'Data', 'connected_apps.json')
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

        # --- NEW: Session memory for staged connections ---
        self.staged_apps = []

    def scan_system_apps(self):
        print("Scanning system for applications...")
        try:
            apps = self.app_manager.scan_installed_apps()
            return {"status": "success", "data": apps, "message": f"Successfully scanned {len(apps)} applications."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- UPDATED: Stages the app in memory instead of saving immediately ---
    def stage_app_connection(self, app_data):
        try:
            with open(self.data_file, 'r') as f:
                permanent_apps = json.load(f)
            
            # Check if already permanently saved
            if any(a['name'] == app_data['name'] for a in permanent_apps):
                return {"status": "info", "message": f"{app_data['name']} is already permanently connected."}
                
            # Check if already staged in this session
            if any(a['name'] == app_data['name'] for a in self.staged_apps):
                return {"status": "info", "message": f"{app_data['name']} is already staged for connection."}

            # Add to temporary staging memory
            app_data['status'] = 'Active'
            app_data['mappings'] = 0
            self.staged_apps.append(app_data)
            
            return {"status": "success", "message": f"Staged {app_data['name']}. Remember to click 'Save Integrations'!"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stage: {str(e)}"}
    
    # --- NEW: Removes an app from the temporary staging memory ---
    def unstage_app_connection(self, app_name):
        initial_count = len(self.staged_apps)
        
        # Filter out the app the user wants to unstage
        self.staged_apps = [a for a in self.staged_apps if a['name'] != app_name]
        
        if len(self.staged_apps) < initial_count:
            return {"status": "success", "message": f"Unstaged {app_name}."}
        else:
            return {"status": "error", "message": f"{app_name} was not staged."}

    # --- NEW: Writes the staged apps to the hard drive ---
    def save_staged_integrations(self):
        if not self.staged_apps:
            return {"status": "error", "message": "No new applications staged to save."}
            
        try:
            with open(self.data_file, 'r') as f:
                apps = json.load(f)
                
            # Append all staged apps to the permanent database
            apps.extend(self.staged_apps)
            
            with open(self.data_file, 'w') as f:
                json.dump(apps, f, indent=4)
                
            saved_count = len(self.staged_apps)
            self.staged_apps.clear() # Clear session after saving
            
            return {"status": "success", "message": f"Successfully saved {saved_count} new integrations!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # --- NEW: Wipes all staged apps if the user cancels ---
    def clear_staged_integrations(self):
        self.staged_apps.clear()
        return {"status": "success", "message": "Cleared all staged integrations."}

    def get_connected_apps(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []
            
    def disconnect_app(self, app_name):
        try:
            with open(self.data_file, 'r') as f:
                apps = json.load(f)
            
            apps = [a for a in apps if a['name'] != app_name]
            
            with open(self.data_file, 'w') as f:
                json.dump(apps, f, indent=4)
            return {"status": "success", "message": f"Disconnected {app_name}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}