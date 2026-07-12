"""Global hotkey registration using pywin32.

Registers Win+Shift+V as a system-wide hotkey. When pressed,
it toggles dictation on/off — even when WhisperType is in the background.
"""
import ctypes
import logging
import threading
from typing import Callable, Optional

import win32con
import win32gui

logger = logging.getLogger(__name__)

# Hotkey IDs
HK_TOGGLE_DICTATION = 1


class HotkeyManager:
    """Manages system-wide hotkey registration on Windows.

    Creates a hidden message-only window to receive WM_HOTKEY messages.
    Runs its own thread with a Windows message pump.

    Usage:
        def on_toggle():
            if recording:
                stop_dictation()
            else:
                start_dictation()

        mgr = HotkeyManager()
        mgr.start(on_toggle)
        # ... app runs ...
        mgr.stop()
    """

    def __init__(self):
        self._hwnd: Optional[int] = None
        self._callback: Optional[Callable[[], None]] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._registered = False

    def start(self, callback: Callable[[], None]):
        """Start listening for the hotkey.

        Args:
            callback: Called (on a background thread) when the hotkey is pressed.
        """
        if self._running:
            return

        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True, name="hotkey-thread")
        self._thread.start()
        logger.info("Hotkey listener started (Win+Shift+V)")

    def stop(self):
        """Stop listening and clean up Windows resources."""
        self._running = False
        if self._hwnd:
            win32gui.PostMessage(self._hwnd, win32con.WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Hotkey listener stopped")

    def _message_loop(self):
        """Windows message pump — runs on a dedicated thread."""
        # Register window class
        wndclass = win32gui.WNDCLASS()
        wndclass.lpfnWndProc = self._wnd_proc
        wndclass.lpszClassName = "WhisperTypeHotkey"
        wndclass.hInstance = win32gui.GetModuleHandle(None)

        try:
            class_atom = win32gui.RegisterClass(wndclass)
        except Exception:
            # Class already registered from a previous run
            class_atom = None

        # Create hidden message-only window
        self._hwnd = win32gui.CreateWindow(
            wndclass.lpszClassName,
            "WhisperTypeHotkey",
            0,
            0, 0, 0, 0,
            0,  # HWND_MESSAGE (message-only)
            0,
            wndclass.hInstance,
            None,
        )

        # Register Win+Shift+V
        modifiers = win32con.MOD_WIN | win32con.MOD_SHIFT
        try:
            if win32gui.RegisterHotKey(self._hwnd, HK_TOGGLE_DICTATION, modifiers, ord("V")):
                self._registered = True
                logger.info("Hotkey registered: Win+Shift+V")
            else:
                logger.error(
                    "Failed to register Win+Shift+V — it may be in use by another app. "
                    "Try changing the hotkey in config.py"
                )
                self._registered = False
        except Exception as e:
            logger.error("Hotkey registration failed: %s (another instance may be running)", e)
            self._registered = False

        # Message loop
        while self._running:
            try:
                msg = win32gui.GetMessage(None, 0, 0)
                if msg:
                    win32gui.TranslateMessage(ctypes.byref(msg))
                    win32gui.DispatchMessage(ctypes.byref(msg))
            except Exception:
                break

        # Cleanup
        if self._hwnd and self._registered:
            win32gui.UnregisterHotKey(self._hwnd, HK_TOGGLE_DICTATION)
        if self._hwnd:
            win32gui.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure — dispatches WM_HOTKEY to our callback."""
        if msg == win32con.WM_HOTKEY and wparam == HK_TOGGLE_DICTATION:
            if self._callback:
                # Run callback in new thread to avoid blocking the message pump
                threading.Thread(target=self._callback, daemon=True).start()
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
