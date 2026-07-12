"""Native Windows overlay pill using tkinter — draggable, minimal, always-on-top.

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
    Draggable: click and drag to reposition.
    """

    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._dot: Optional[int] = None
        self._label: Optional[int] = None
        self._running = False
        self._status = "idle"
        self._drag_x = 0
        self._drag_y = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Create and show the pill window."""
        if self._running:
            return

        self._running = True
        self._root = tk.Tk()
        self._root.title("")
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-toolwindow", True)

        bg = "#0f0f14"
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        w, h = 168, 34
        x = screen_w - w - 16
        y = screen_h - h - 64
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=w, height=h,
            bg=bg, highlightthickness=1,
            highlightbackground="#2a2a35", bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        # Dot
        dot_x, dot_y = 14, h // 2
        self._dot = self._canvas.create_oval(
            dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4,
            fill="#22c55e", outline="", tags="dot",
        )

        # Label
        self._label = self._canvas.create_text(
            30, h // 2, text="Ready", fill="#a0a0b0",
            font=("Segoe UI", 9), anchor="w", tags="label",
        )

        # Close button (×)
        self._canvas.create_text(
            w - 12, h // 2, text="×", fill="#555",
            font=("Segoe UI", 11, "bold"), anchor="e",
            tags="close",
        )
        self._canvas.tag_bind("close", "<Button-1>", lambda e: self.stop())

        # Drag bindings
        self._canvas.bind("<Button-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_move)
        self._canvas.bind("<Button-3>", lambda e: self.stop())  # right-click to close
        # Also bind on the window
        self._root.bind("<Button-1>", self._on_drag_start)
        self._root.bind("<B1-Motion>", self._on_drag_move)

        self._draw()

        threading.Thread(target=self._ws_listener, daemon=True).start()
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

    def _draw(self):
        if not self._root or not self._canvas:
            return

        import time, math
        t = time.time()

        if self._status == "recording":
            pulse = 0.5 + 0.5 * (math.sin(t * 4) ** 2)
            r, g, b = int(200 + 55 * pulse), int(40 * (1 - pulse)), int(40 * (1 - pulse))
            color = f"#{r:02x}{g:02x}{b:02x}"
            text = "Recording"
        elif self._status == "transcribing":
            color = "#eab308"
            text = "Transcribing"
        else:
            color = "#22c55e"
            text = "Ready"

        self._canvas.itemconfig(self._dot, fill=color)
        self._canvas.itemconfig(self._label, text=text)

        if self._running:
            self._root.after(100, self._draw)

    def stop(self):
        self._running = False
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception:
                pass

    def _ws_listener(self):
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
                        import time; time.sleep(1)
        except Exception as e:
            logger.debug("Pill WS: %s", e)


pill = PillOverlay()


def start_pill():
    if pill.is_running:
        return
    t = threading.Thread(target=pill.start, daemon=True, name="pill-thread")
    t.start()
    logger.info("Pill overlay started")


def stop_pill():
    pill.stop()
    logger.info("Pill overlay stopped")


def toggle_pill():
    if pill.is_running:
        stop_pill()
        return "closed"
    else:
        start_pill()
        return "opened"
