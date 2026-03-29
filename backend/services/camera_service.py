import cv2
import mediapipe as mp
import threading
import base64

class CameraService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern: ensures only one camera service exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraService, cls).__new__(cls)
                cls._instance._init_camera_service()
        return cls._instance

    def _init_camera_service(self):
        """Internal initialization logic."""
        self.is_scanning = False
        self.current_frame = None
        self.hand_detected = False
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

    def start(self, frame_callback):
        if not self.is_scanning:
            self.is_scanning = True
            # Hardware remains isolated in a single daemon thread
            threading.Thread(target=self._run_loop, args=(frame_callback,), daemon=True).start()

    def stop(self):
        self.is_scanning = False

    def _run_loop(self, callback):
        # CAP_DSHOW is added for faster initialization on Windows
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        while self.is_scanning:
            success, frame = cap.read()
            if not success or not self.is_scanning: 
                break
            
            frame = cv2.flip(frame, 1)
            self.current_frame = frame.copy()
            results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            confidence = 0
            if results.multi_hand_landmarks:
                self.hand_detected = True
                if results.multi_handedness:
                    confidence = int(results.multi_handedness[0].classification[0].score * 100)
                for handLms in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, handLms, self.mp_hands.HAND_CONNECTIONS)
            else:
                self.hand_detected = False
                
            _, buffer = cv2.imencode('.jpg', frame)
            callback(base64.b64encode(buffer).decode('utf-8'), confidence)
        
        cap.release()