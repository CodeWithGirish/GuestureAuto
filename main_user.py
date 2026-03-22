import webview
import os
from gesture_api import GestureAutoAPI  # Import the separated logic

def start_user_app():
    # 1. Define the path to the Scan Screen
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scan_screen_path = os.path.join(current_dir, 'frontend', 'user_app', '2_Gusture Module', '2_Guesture Scan Screen.html')

    # 2. Instantiate the imported API
    api = GestureAutoAPI()

    # 3. Create and start the webview window
    window = webview.create_window(
        title='GestureAuto - Gesture Scan', 
        url=f'file://{scan_screen_path}',
        width=1280, 
        height=800,
        min_size=(1024, 768),
        js_api=api 
    )
    
    # Start the application
    webview.start()

if __name__ == '__main__':
    start_user_app()