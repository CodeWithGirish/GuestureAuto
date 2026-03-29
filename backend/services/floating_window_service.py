import webview

class FloatingWindowService:
    def __init__(self):
        self.window = None

    def show_float_window(self):
        """Creates the window only when this method is invoked."""
        if self.window:
            return # Prevent duplicate windows if already open

        self.window = webview.create_window(
            'Live Feed',
            url='frontend/user_app/2_Gusture Module/float_camera.html',
            width=300,
            height=200,
            on_top=True,
            frameless=True,
            easy_drag=True
        )
        # Reset the reference if the user closes the window manually
        self.window.events.closed += self._reset_window_ref

    def _reset_window_ref(self):
        self.window = None

    def close_float_window(self):
        """Safely destroys the window."""
        if self.window:
            self.window.destroy()
            self.window = None