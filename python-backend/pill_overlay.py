"""Native Windows overlay pill using tkinter — properly layered, always-on-top.

Voquill uses Direct2D via Rust. We use tkinter (native Win32 under the hood) 
for the same effect — frameless popup, no white box, proper rendering.
"""
import logging
import threading
import tkinter as tk
from typing import Optional

logger = logging.getLogger(__name__)


class PillOverlay:
    """A small always-on-top frameless window showing dictation status.

    Green dot = idle, Red pulsing dot = recording, Yellow = transcribing.
    """

    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._dot: Optional[int] = None
        self._label: Optional[int] = None
        self._running = False
        self._status = "idle"  # idle | recording | transcribing

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Create and show the pill window."""
        if self._running:
            return

        self._running = True
        self._root = tk.Tk()
        self._root.title("WhisperType Pill")
        self._root.overrideredirect(True)  # Frameless
        self._root.attributes("-topmost", True)  # Always on top
        self._root.attributes("-toolwindow", True)  # No taskbar entry

        # Dark background
        bg = "#0f0f14"

        # Position bottom-right
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        w, h = 280, 44
        x = screen_w - w - 16
        y = screen_h - h - 64
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        # Canvas for drawing
        self._canvas = tk.Canvas(
            self._root,
            width=w, height=h,
            bg=bg,
            highlightthickness=1,
            highlightbackground="#2a2a35",
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        # Draw background with rounded corners effect
        self._canvas.create_rectangle(4, 4, w - 4, h - 4, fill=bg, outline="", tags="bg")

        # Status dot (green initially)
        dot_x, dot_y = 18, h // 2
        self._dot = self._canvas.create_oval(
            dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5,
            fill="#22c55e", outline="", tags="dot",
        )

        # Status label
        self._label = self._canvas.create_text(
            38, h // 2,
            text="Ready",
            fill="#a0a0b0",
            font=("Segoe UI", 10),
            anchor="w",
            tags="label",
        )

        self._draw()

        # Start WebSocket listener in background
        threading.Thread(target=self._ws_listener, daemon=True).start()

        # Enter tkinter main loop
        self._root.mainloop()
        self._running = False

    def _draw(self):
        """Redraw animation frame (pulsing effect when recording)."""
        if not self._root or not self._canvas:
            return

        import time
        t = time.time()

        if self._status == "recording":
            # Pulsing red
            pulse = 0.5 + 0.5 * (__import__("math").sin(t * 4) ** 2)
            r = int(200 + 55 * pulse)
            g = int(40 * (1 - pulse))
            b = int(40 * (1 - pulse))
            color = f"#{r:02x}{g:02x}{b:02x}"
            text = "Recording..."
        elif self._status == "transcribing":
            color = "#eab308"  # Yellow
            text = "Transcribing..."
        else:
            color = "#22c55e"  # Green
            text = "Ready"

        self._canvas.itemconfig(self._dot, fill=color)
        self._canvas.itemconfig(self._label, text=text)

        # Schedule next frame
        if self._running:
            self._root.after(100, self._draw)

    def stop(self):
        """Close the pill window."""
        self._running = False
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception:
                pass

    def _ws_listener(self):
        """Background thread: connect to WebSocket for status updates."""
        try:
            import json
            from websocket import create_connection

            ws = create_connection("ws://127.0.0.1:9877/api/ws", timeout=5)
            while self._running:
                try:
                    msg = ws.recv()
                    data = json.loads(msg)
                    if data.get("type") == "status":
                        if data.get("isRecording"):
                            self._status = "recording"
                        elif data.get("state") == "transcribing":
                            self._status = "transcribing"
                        else:
                            self._status = "idle"
                except Exception:
                    if not self._running:
                        break
                    try:
                        ws = create_connection("ws://127.0.0.1:9877/api/ws", timeout=5)
                    except Exception:
                        import time
                        time.sleep(1)
        except Exception as e:
            logger.debug("Pill WebSocket: %s", e)


# Global instance
pill = PillOverlay()


def start_pill():
    """Start the pill in a background thread."""
    if pill.is_running:
        return
    t = threading.Thread(target=pill.start, daemon=True, name="pill-thread")
    t.start()
    logger.info("Pill overlay started")


def stop_pill():
    """Stop the pill."""
    pill.stop()
    logger.info("Pill overlay stopped")


def toggle_pill():
    """Toggle the pill on/off."""
    if pill.is_running:
        stop_pill()
        return "closed"
    else:
        start_pill()
        return "opened"
