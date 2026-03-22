import cv2
import base64
import threading
import mediapipe as mp
import webview
import os
import json

class GestureAutoAPI:
    def __init__(self):
        self.is_scanning = False
        self.scan_thread = None
        self.current_frame = None 
        self.hand_detected = False # NEW: Flag to track if a hand is currently in frame
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.dataset_dir = os.path.join(os.path.dirname(__file__), 'Data', 'sample_images')
        os.makedirs(self.dataset_dir, exist_ok=True)

    def start_scan(self):
        if not self.is_scanning:
            print("Starting Camera Stream...")
            self.is_scanning = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
        return {"status": "success", "message": "Scanning Started"}

    def stop_scan(self):
        print("Stopping Camera Stream...")
        self.is_scanning = False
        return {"status": "success", "message": "Scanning Stopped"}

    def capture_image(self, gesture_name):
        if not self.is_scanning or self.current_frame is None:
            return {"status": "error", "message": "Please start the scanner first."}
            
        # NEW: Block capture if no hand is visible
        if not self.hand_detected:
            return {"status": "error", "message": "No hand detected! Please show your hand in the frame to capture."}
        
        safe_name = "".join([c for c in gesture_name if c.isalpha() or c.isdigit() or c==' ']).strip()
        if not safe_name:
            safe_name = "Unknown_Gesture"
            
        gesture_folder = os.path.join(self.dataset_dir, safe_name)
        os.makedirs(gesture_folder, exist_ok=True)
        
        existing_files = len(os.listdir(gesture_folder))
        filename = f"{safe_name.replace(' ', '_')}_{existing_files + 1}.jpg"
        filepath = os.path.join(gesture_folder, filename)
        
        cv2.imwrite(filepath, self.current_frame)
        print(f"Captured and saved: {filepath}")
        
        _, buffer = cv2.imencode('.jpg', self.current_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        img_data = {
            "base64": f"data:image/jpeg;base64,{img_base64}",
            "filepath": filepath
        }
        try:
            if len(webview.windows) > 0:
                window = webview.windows[0]
                window.evaluate_js(f"addScannedImage({json.dumps(img_data)})")
        except Exception as e:
            print("Failed to update image gallery:", e)

        return {"status": "success", "message": f"Saved {filename}"}

    def delete_images(self, filepaths):
        deleted_count = 0
        for path in filepaths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting {path}: {e}")
        return {"status": "success", "message": f"Successfully deleted {deleted_count} images."}

    def _scan_loop(self):
        cap = cv2.VideoCapture(0)
        
        while self.is_scanning:
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            
            # SAVE A CLEAN COPY BEFORE DRAWING LANDMARKS
            self.current_frame = frame.copy() 
            
            imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(imgRGB)
            
            confidence = 0

            # NEW: Extract real confidence from MediaPipe's handedness data
            if results.multi_hand_landmarks and results.multi_handedness:
                self.hand_detected = True
                
                # Get the confidence score of the first detected hand
                # MediaPipe returns a float like 0.9543, so we multiply by 100 and convert to integer
                raw_score = results.multi_handedness[0].classification[0].score
                confidence = int(raw_score * 100)
                
                for handLms in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, handLms, self.mp_hands.HAND_CONNECTIONS)
            else:
                self.hand_detected = False
            
            _, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode('utf-8')

            try:
                if len(webview.windows) > 0:
                    window = webview.windows[0]
                    window.evaluate_js(f"updateFrame('data:image/jpeg;base64,{img_str}')")
                    window.evaluate_js(f"updateGestureMetrics({confidence})")
            except Exception as e:
                print("UI update failed:", e)

        cap.release()
        if len(webview.windows) > 0:
            webview.windows[0].evaluate_js("clearFrame()")