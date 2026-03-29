import cv2
import base64
import threading
import mediapipe as mp
import webview
import os
import json
import shutil

class GestureAutoAPI:
    def __init__(self):
        self.is_scanning = False
        self.scan_thread = None
        self.current_frame = None 
        self.hand_detected = False 
        
        self.session_frames = {} 
        self.frame_counter = 0   
        self.editing_gesture = None # NEW: Tracks the gesture currently being edited
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

        self.dataset_dir = os.path.join(os.path.dirname(__file__), 'Data', 'sample_images')
        os.makedirs(self.dataset_dir, exist_ok=True)

    def start_scan(self):
        if not self.is_scanning:
            self.is_scanning = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
        return {"status": "success"}

    def stop_scan(self):
        self.is_scanning = False
        return {"status": "success"}

    def capture_image(self):
        if not self.is_scanning or self.current_frame is None:
            return {"status": "error", "message": "Please start the scanner first."}
        if not self.hand_detected:
            return {"status": "error", "message": "No hand detected! Please show your hand in the frame."}
        
        temp_id = f"frame_{self.frame_counter}"
        self.session_frames[temp_id] = self.current_frame.copy()
        self.frame_counter += 1
        
        _, buffer = cv2.imencode('.jpg', self.current_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        img_data = {"base64": f"data:image/jpeg;base64,{img_base64}", "temp_id": temp_id}
        
        try:
            if len(webview.windows) > 0:
                webview.windows[0].evaluate_js(f"addScannedImage({json.dumps(img_data)})")
        except Exception as e:
            pass
        return {"status": "success"}

    # --- NEW: Sets the active edit state ---
    def edit_gesture(self, gesture_name):
        self.editing_gesture = gesture_name
        return {"status": "success"}

    # --- NEW: Loads existing images into memory when Scan screen opens ---
    def get_current_session(self):
        data = {"gesture_name": "", "frames": []}
        
        # If we aren't editing anything, return empty data
        if not self.editing_gesture:
            return data
            
        data["gesture_name"] = self.editing_gesture
        self.session_frames.clear()
        self.frame_counter = 0
        
        folder_path = os.path.join(self.dataset_dir, self.editing_gesture)
        if os.path.exists(folder_path):
            images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
            for img_name in images:
                img_path = os.path.join(folder_path, img_name)
                frame = cv2.imread(img_path)
                if frame is not None:
                    temp_id = f"frame_{self.frame_counter}"
                    self.session_frames[temp_id] = frame
                    self.frame_counter += 1
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    data["frames"].append({"temp_id": temp_id, "base64": f"data:image/jpeg;base64,{img_base64}"})
                    
        return data

    def save_session(self, gesture_name):
        if not self.session_frames:
            return {"status": "error", "message": "No frames to save."}

        safe_name = "".join([c for c in gesture_name if c.isalpha() or c.isdigit() or c==' ']).strip()
        gesture_folder = os.path.join(self.dataset_dir, safe_name)
        
        # UPDATED: Wipe the existing folder before saving to perfectly sync UI deletions to the disk
        if os.path.exists(gesture_folder):
            shutil.rmtree(gesture_folder)
        os.makedirs(gesture_folder, exist_ok=True)
        
        saved_count = 0
        for tid, frame in self.session_frames.items():
            filename = f"{safe_name.replace(' ', '_')}_{saved_count + 1}.jpg"
            filepath = os.path.join(gesture_folder, filename)
            cv2.imwrite(filepath, frame)
            saved_count += 1

        self.session_frames.clear()
        self.editing_gesture = None # Clear edit state after saving
        return {"status": "success", "message": f"Successfully saved {saved_count} images."}

    def delete_images(self, temp_ids):
        for tid in temp_ids:
            if tid in self.session_frames:
                del self.session_frames[tid]
        return {"status": "success"}

    def clear_session(self):
        self.session_frames.clear()
        self.editing_gesture = None
        return {"status": "success"}

    def delete_gesture(self, gesture_name):
        folder_path = os.path.join(self.dataset_dir, gesture_name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            return {"status": "success"}
        return {"status": "error"}

    def get_saved_gestures(self):
        gestures = []
        if not os.path.exists(self.dataset_dir): return gestures
        for folder_name in os.listdir(self.dataset_dir):
            folder_path = os.path.join(self.dataset_dir, folder_name)
            if os.path.isdir(folder_path):
                images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png'))]
                count = len(images)
                thumbnail = ""
                if count > 0:
                    with open(os.path.join(folder_path, images[0]), "rb") as f:
                        thumbnail = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
                gestures.append({"name": folder_name, "count": count, "thumbnail": thumbnail})
        return gestures
    # --- UPDATED: Deletes images, and removes folder if empty ---
    def delete_saved_images(self, gesture_name, filenames):
        if not gesture_name or not filenames:
            return {"status": "error", "message": "Invalid request."}
            
        folder_path = os.path.join(self.dataset_dir, gesture_name)
        deleted_count = 0
        folder_deleted = False # Flag to tell JS what happened
        
        if os.path.exists(folder_path):
            for filename in filenames:
                safe_filename = os.path.basename(filename) 
                file_path = os.path.join(folder_path, safe_filename)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
            
            # --- NEW: Check if folder is empty after deletion ---
            remaining_images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
            if len(remaining_images) == 0:
                try:
                    shutil.rmtree(folder_path)
                    print(f"Folder '{gesture_name}' is empty. Deleted automatically.")
                    folder_deleted = True
                except Exception as e:
                    print(f"Error removing empty folder: {e}")
                    
        return {
            "status": "success", 
            "message": f"Deleted {deleted_count} images.", 
            "folder_deleted": folder_deleted # Send flag back to UI
        }

    # --- NEW: Fetches all images for a specific gesture to display in the modal ---
    def get_gesture_images(self, gesture_name):
        images_data = []
        folder_path = os.path.join(self.dataset_dir, gesture_name)
        
        if os.path.exists(folder_path):
            images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
            for img_name in images:
                img_path = os.path.join(folder_path, img_name)
                try:
                    with open(img_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode('utf-8')
                        images_data.append({
                            "filename": img_name,
                            "base64": f"data:image/jpeg;base64,{encoded}"
                        })
                except Exception as e:
                    print(f"Error loading {img_name}: {e}")
                    
        return {"gesture_name": gesture_name, "images": images_data}
    def _scan_loop(self):
        cap = cv2.VideoCapture(0)
        while self.is_scanning:
            success, frame = cap.read()
            if not success: continue
            frame = cv2.flip(frame, 1)
            self.current_frame = frame.copy() 
            imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(imgRGB)
            confidence = 0
            if results.multi_hand_landmarks and results.multi_handedness:
                self.hand_detected = True
                confidence = int(results.multi_handedness[0].classification[0].score * 100)
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
            except: pass
        cap.release()
        if len(webview.windows) > 0:
            webview.windows[0].evaluate_js("clearFrame()")