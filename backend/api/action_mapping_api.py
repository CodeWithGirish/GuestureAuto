from backend.services.action_mapping_service import ActionMappingService

class ActionMappingAPI:
    def __init__(self):
        self.service = ActionMappingService()

    def get_mappings(self):
        return self.service.get_mappings()

    def save_mapping(self, mapping_data):
        return self.service.save_mapping(mapping_data)

    # UPDATED: Add target_app argument here
    def delete_mapping(self, gesture_name, target_app="Global"):
        return self.service.delete_mapping(gesture_name, target_app)