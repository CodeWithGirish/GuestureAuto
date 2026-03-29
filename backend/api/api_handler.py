from backend.api.gesture_api import GestureAutoAPI
from backend.api.integration_api import IntegrationAPI
from backend.services.camera_service import CameraService
from backend.api.action_mapping_api import ActionMappingAPI

class MasterAPI:
    """This class bundles all APIs together for the frontend."""
    def __init__(self):
        # Resource Fix: Sharing the Singleton camera service across modules
        self.camera_service = CameraService() 
        self.gesture_api = GestureAutoAPI()
        self.integration_api = IntegrationAPI()
        # --- NEW INSTANCE ---
        self.action_mapping_api = ActionMappingAPI()

    # ==========================================
    # ACTION MAPPING MODULE METHODS
    # ==========================================
    def get_mappings(self):
        return self.action_mapping_api.get_mappings()

    def save_mapping(self, mapping_data):
        return self.action_mapping_api.save_mapping(mapping_data)

    # UPDATED: Add target_app argument here
    def delete_mapping(self, gesture_name, target_app="Global"):
        return self.action_mapping_api.delete_mapping(gesture_name, target_app)


    # ==========================================
    # INTEGRATION MODULE METHODS (Preserved)
    # ==========================================
    def scan_system_apps(self):
        return self.integration_api.scan_system_apps()

    def stage_app_connection(self, app_data):
        return self.integration_api.stage_app_connection(app_data)

    def unstage_app_connection(self, app_name):
        return self.integration_api.unstage_app_connection(app_name)

    def save_staged_integrations(self):
        return self.integration_api.save_staged_integrations()

    def clear_staged_integrations(self):
        return self.integration_api.clear_staged_integrations()

    def get_connected_apps(self):
        return self.integration_api.get_connected_apps()

    def disconnect_app(self, app_name):
        return self.integration_api.disconnect_app(app_name)

    # ==========================================
    # GESTURE MODULE METHODS (Fixing Bridge Flaws)
    # ==========================================
    def get_current_session(self):
        """Fixes TypeError: pywebview.api.get_current_session is not a function"""
        return self.gesture_api.get_current_session()

    def capture_image(self):
        """Bridges the manual image capture trigger"""
        return self.gesture_api.capture_image()

    def delete_images(self, temp_ids):
        """Fixes TypeError: pywebview.api.delete_images is not a function"""
        return self.gesture_api.delete_images(temp_ids)

    def edit_gesture(self, gesture_name):
        """Fixes TypeError: pywebview.api.edit_gesture is not a function"""
        return self.gesture_api.edit_gesture(gesture_name)

    def delete_gesture(self, gesture_name):
        """Fixes TypeError: pywebview.api.delete_gesture is not a function"""
        return self.gesture_api.delete_gesture(gesture_name)

    def get_gesture_images(self, gesture_name):
        """Fixes TypeError: pywebview.api.get_gesture_images is not a function"""
        return self.gesture_api.get_gesture_images(gesture_name)

    def delete_saved_images(self, gesture_name, filenames):
        """Fixes TypeError: pywebview.api.delete_saved_images is not a function"""
        return self.gesture_api.delete_saved_images(gesture_name, filenames)

    def start_scan(self):
        return self.gesture_api.start_scan()

    def stop_scan(self):
        return self.gesture_api.stop_scan()

    def get_saved_gestures(self):
        return self.gesture_api.get_saved_gestures()

    def save_session(self, gesture_name):
        return self.gesture_api.save_session(gesture_name)

    def shutdown(self):
        """Architectural Fix: Centralized cleanup for singleton resources."""
        self.gesture_api.stop_scan()
        self.camera_service.stop()