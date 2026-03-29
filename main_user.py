import webview
import os
from backend.api.api_handler import MasterAPI 

def main():
    api = MasterAPI()
    root = os.path.dirname(os.path.abspath(__file__))
    
    # Absolute pathing fixes the "File Not Found" architectural flaw
    ui_path = os.path.join(root, 'frontend', 'user_app', '3_Action Mapping', '2_Create Mapping Screen.html')

    window = webview.create_window(
        title='GestureAuto', 
        url=f'file://{ui_path}', 
        js_api=api,
        width=1280, 
        height=800
    )

    try:
        webview.start(debug=True)
    finally:
        # RESOURCE FIX: Ensures camera thread stops on window close
        api.shutdown()

if __name__ == '__main__':
    main()