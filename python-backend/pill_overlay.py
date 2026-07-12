"""Native Windows overlay pill — draggable, always-on-top, minimal.

Auto-starts with the backend. Position persists between sessions.
Blue dot (calm) instead of green. No manual toggle needed.
"""
import json
import logging
import os
import threading
import tkinter as tk
from typing import Optional

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "pill_position.json")


def _load_position():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def _save_position(x, y):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"x": x, "y": y}, f)
    except Exception:
        pass


class PillOverlay:
    """Frameless always-on-top overlay showing dictation status."""

    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._dot: Optional[int] = None
        self._label: Optional[int] = None
        self._running = False
        self._status = "idle"
        self._drag_x = 0
        self._drag_y = 0
        self._ws_thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Create and show the pill. Safe to call multiple times — ignores if already running."""
        if self._running:
            return

        self._running = True
        self._root = tk.Tk()
        self._root.title("")
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-toolwindow", True)
        self._root.protocol("WM_DELETE_WINDOW", self.stop)

        bg = "#0f0f14"
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        w, h = 150, 30

        # Restore saved position or default to bottom-right
        saved = _load_position()
        if saved:
            x, y = saved["x"], saved["y"]
            # Clamp to screen
            x = max(0, min(x, screen_w - w))
            y = max(0, min(y, screen_h - h))
        else:
            x = screen_w - w - 16
            y = screen_h - h - 64

        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=w, height=h,
            bg=bg, highlightthickness=1,
            highlightbackground="#2a2a35", bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        # Blue dot (calmer)
        dot_x, dot_y = 12, h // 2
        self._dot = self._canvas.create_oval(
            dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4,
            fill="#3b82f6", outline="", tags="dot",
        )

        # Label
        self._label = self._canvas.create_text(
            26, h // 2, text="Ready", fill="#a0a0b0",
            font=("Segoe UI", 8), anchor="w", tags="label",
        )

        # Close ×
        self._canvas.create_text(
            w - 10, h // 2, text="×", fill="#555",
            font=("Segoe UI", 10, "bold"), anchor="e", tags="close",
        )
        self._canvas.tag_bind("close", "<Button-1>", lambda e: self.stop())

        # Drag
        self._canvas.bind("<Button-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_move)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._root.bind("<Button-1>", self._on_drag_start)
        self._root.bind("<B1-Motion>", self._on_drag_move)
        self._root.bind("<ButtonRelease-1>", self._on_drag_end)
        self._root.bind("<Button-3>", lambda e: self.stop())

        self._draw()
        self._ws_thread = threading.Thread(target=self._ws_listener, daemon=True)
        self._ws_thread.start()
        self._root.mainloop()
        self._running = False

    def _on_drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_move(self, event):
        if not self._root:
            return
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self._root.winfo_x() + dx
        y = self._root.winfo_y() + dy
        self._root.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        if self._root:
            _save_position(self._root.winfo_x(), self._root.winfo_y())

    def _draw(self):
        if not self._root or not self._canvas:
            return

        import time, math
        t = time.time()

        if self._status == "recording":
            pulse = 0.5 + 0.5 * (math.sin(t * 4) ** 2)
            r, g, b = int(59 + 100 * pulse), int(130 - 60 * pulse), int(246 - 80 * pulse)
            color = f"#{r:02x}{g:02x}{b:02x}"
            text = "Recording"
        elif self._status == "transcribing":
            color = "#eab308"
            text = "Transcribing"
        else:
            color = "#3b82f6"
            text = "Ready"

        self._canvas.itemconfig(self._dot, fill=color)
        self._canvas.itemconfig(self._label, text=text)

        if self._running:
            self._root.after(100, self._draw)

    def stop(self):
        """Safely close the pill window."""
        self._running = False
        root = self._root
        self._root = None
        self._canvas = None
        if root:
            try:
                root.quit()
                root.destroy()
            except Exception:
                pass

    def _ws_listener(self):
        try:
            import json as _json
            from websocket import create_connection
            ws = create_connection("ws://127.0.0.1:9877/api/ws", timeout=5)
            while self._running:
                try:
                    msg = ws.recv()
                    data = _json.loads(msg)
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
                        import time; time.sleep(1)
        except Exception as e:
            logger.debug("Pill WS: %s", e)


# Global singleton — only ONE instance
_pill: Optional[PillOverlay] = None
_pill_lock = threading.Lock()


def start_pill():
    """Start the pill overlay. Thread-safe — ignores duplicate calls."""
    global _pill
    with _pill_lock:
        if _pill is not None and _pill.is_running:
            return
        if _pill is not None:
            _pill.stop()
        _pill = PillOverlay()
    t = threading.Thread(target=_pill.start, daemon=True, name="pill")
    t.start()
    logger.info("Pill overlay started")


def stop_pill():
    """Stop the pill overlay."""
    global _pill
    with _pill_lock:
        if _pill:
            _pill.stop()
            _pill = None
    logger.info("Pill overlay stopped")


def toggle_pill():
    """Toggle pill on/off. Returns status string."""
    global _pill
    with _pill_lock:
        if _pill and _pill.is_running:
            stop_pill()
            return "closed"
    start_pill()
    return "opened"
