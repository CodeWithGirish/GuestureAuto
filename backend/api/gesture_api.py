import webview
import json
import base64
import cv2
import os
from ..services.camera_service import CameraService
from ..services.storage_service import StorageService
from ..services.floating_window_service import FloatingWindowService

class GestureAutoAPI:
    def __init__(self):
        self.camera = CameraService()
        self.storage = StorageService()
        self.float_service = FloatingWindowService()
        self.session_frames = {}
        self.frame_counter = 0
        self.editing_gesture = None

    def toggle_float_window(self):
        """Starts the float window service only when explicitly called."""
        # Ensure the system is actually scanning in the backend for safety
        if self.camera.is_scanning:
            self.float_service.show_float_window()
            return {"status": "success"}
        return {"status": "error", "message": "System not started"}

    def start_scan(self):
        if not self.camera.is_scanning:
            self.camera.start(self._ui_frame_callback) # Starts OpenCV/MediaPipe thread
        return {"status": "success"} # Returns signal to JS

    def stop_scan(self):
        """Stops the camera and forces the float window to close."""
        self.camera.stop()
        # Automatically clean up the float window if the system stops
        self.float_service.close_float_window()
        return {"status": "success"}

    # backend/api/gesture_api.py

    def _ui_frame_callback(self, img_b64, confidence):
        """Broadcasts the camera feed to all open pywebview windows."""
        if webview.windows:
            # Loop through every active window (Main, Float, etc.)
            for window in webview.windows:
                try:
                    # Wrap in a check to see if the window has the updateFrame function
                    js_command = f"""
                    if (typeof updateFrame !== 'undefined') {{
                        updateFrame('data:image/jpeg;base64,{img_b64}');
                        if (typeof updateGestureMetrics !== 'undefined') {{
                            updateGestureMetrics({confidence});
                        }}
                    }}
                """
                    window.evaluate_js(js_command)
                except Exception as e:
                    # Ignore windows that are currently closing or transitioning
                    pass    

    def get_current_session(self):
        """Loads existing images into session memory for the Scan Screen."""
        data = {"gesture_name": self.editing_gesture or "", "frames": []}
        if not self.editing_gesture:
            return data
        self.session_frames.clear()
        self.frame_counter = 0
        folder_path = os.path.join(self.storage.dataset_dir, self.editing_gesture)
        if os.path.exists(folder_path):
            images = sorted([f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))])
            for img_name in images:
                frame = cv2.imread(os.path.join(folder_path, img_name))
                if frame is not None:
                    tid = f"frame_{self.frame_counter}"
                    self.session_frames[tid] = frame
                    _, buf = cv2.imencode('.jpg', frame)
                    img_b64 = base64.b64encode(buf).decode('utf-8')
                    data["frames"].append({"temp_id": tid, "base64": f"data:image/jpeg;base64,{img_b64}"})
                    self.frame_counter += 1
        return data

    def capture_image(self):
        if not self.camera.is_scanning or self.camera.current_frame is None:
            return {"status": "error", "message": "Camera not active."}
        tid = f"frame_{self.frame_counter}"
        self.session_frames[tid] = self.camera.current_frame.copy()
        self.frame_counter += 1
        _, buf = cv2.imencode('.jpg', self.camera.current_frame)
        img_b64 = base64.b64encode(buf).decode('utf-8')
        data = {"base64": f"data:image/jpeg;base64,{img_b64}", "temp_id": tid}
        if webview.windows:
            webview.windows[0].evaluate_js(f"addScannedImage({json.dumps(data)})")
        return {"status": "success"}

    def clear_session(self):
        """Clears the capture buffer."""
        self.session_frames.clear()
        self.frame_counter = 0
        return {"status": "success"}

    def delete_images(self, temp_ids):
        """Removes selected images from the session."""
        for tid in temp_ids:
            if tid in self.session_frames:
                del self.session_frames[tid]
        return {"status": "success"}

    def save_session(self, gesture_name):
        """Saves session and automatically redirects the user."""
        # 1. Perform the save operation
        count = self.storage.save_session_to_disk(gesture_name, self.session_frames)
        
        # 2. Reset the backend state
        self.session_frames.clear()
        self.frame_counter = 0
        self.editing_gesture = None
        self.camera.stop()
        
        # 3. Trigger redirection in the frontend
        if webview.windows:
            # Path is relative to the current HTML file's location
            # Since we are in '2_Gusture Module/2_Guesture Scan Screen.html',
            # we stay in the same folder to reach '1_Saved Guesture Screen.html'
            redirection_script = "window.location.href = '1_Saved Guesture Screen.html';"
            webview.windows[0].evaluate_js(redirection_script)
            
        return {"status": "success", "message": f"Saved {count} images and redirecting..."}

    def get_saved_gestures(self):
        return self.storage.get_all_gestures()

    def get_gesture_images(self, gesture_name):
        return self.storage.get_gesture_sample_images(gesture_name)

    def delete_saved_images(self, gesture_name, filenames):
        count, removed = self.storage.delete_specific_images(gesture_name, filenames)
        return {"status": "success", "message": f"Deleted {count} images.", "folder_deleted": removed}

    def delete_gesture(self, name):
        if self.storage.delete_gesture_folder(name):
            return {"status": "success"}
        return {"status": "error"}

    def edit_gesture(self, name):
        self.editing_gesture = name
        return {"status": "success"}