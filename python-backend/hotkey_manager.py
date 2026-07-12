"""Global hotkey using low-level keyboard hook (SetWindowsHookEx).

Same approach as Voquill's rdev::grab — intercepts all keystrokes at the OS level,
checks for the target combo, and triggers the callback. No RegisterHotKey conflicts.
"""
import ctypes
import logging
import threading
from ctypes import wintypes
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Windows constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_F12 = 0x7B

# Target combo: Ctrl+Shift+F12
TARGET_MODS = {VK_CONTROL, VK_SHIFT}
TARGET_KEY = VK_F12

# Low-level keyboard hook struct
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

# Callback type
LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT)
)

# Windows DLLs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class LowLevelHotkey:
    """Hotkey via SetWindowsHookEx — no RegisterHotKey conflicts.

    Usage:
        def on_toggle():
            print("Hotkey pressed!")

        hotkey = LowLevelHotkey()
        hotkey.start(on_toggle)
        # ... app runs ...
        hotkey.stop()
    """

    def __init__(self):
        self._hook_id: Optional[int] = None
        self._callback: Optional[Callable[[], None]] = None
        self._running = False
        self._pressed_keys: set[int] = set()
        self._hook_proc = LowLevelKeyboardProc(self._hook_callback)
        # Prevent GC of the callback
        self._hook_proc_ref = self._hook_proc

    def start(self, callback: Callable[[], None]):
        """Install the low-level keyboard hook."""
        if self._running:
            return

        self._callback = callback
        self._running = True

        # Install the hook
        self._hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            kernel32.GetModuleHandleW(None),
            0,  # 0 = global hook for low-level hooks
        )

        if not self._hook_id:
            error = kernel32.GetLastError()
            logger.error("SetWindowsHookEx failed: error %d", error)
            self._running = False
            return

        logger.info("Low-level keyboard hook installed (Ctrl+Shift+F12)")

        # Run Windows message pump in this thread to keep the hook alive
        msg = wintypes.MSG()
        while self._running:
            # PeekMessage instead of GetMessage so we can check self._running
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

    def stop(self):
        """Remove the hook and stop the message pump."""
        self._running = False

        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None

        # Post a dummy message to wake up PeekMessage loop
        user32.PostThreadMessageW(kernel32.GetCurrentThreadId(), 0, 0, 0)

        logger.info("Keyboard hook removed")

    def _hook_callback(self, nCode: int, wParam: wintypes.WPARAM, lParam: ctypes.POINTER(KBDLLHOOKSTRUCT)) -> int:
        """Called by Windows for every keyboard event."""
        if nCode < 0:
            return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

        kb = lParam.contents
        vk = kb.vkCode

        if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            self._pressed_keys.add(vk)

            # Check if target combo is pressed
            mods_pressed = bool(TARGET_MODS & self._pressed_keys)  # at least one mod
            all_mods_pressed = TARGET_MODS.issubset(self._pressed_keys)
            target_pressed = TARGET_KEY in self._pressed_keys

            if all_mods_pressed and target_pressed and self._callback:
                # Fire callback in a new thread to not block the hook
                threading.Thread(target=self._callback, daemon=True).start()
                # Clear F12 so we don't re-fire while held
                self._pressed_keys.discard(TARGET_KEY)

        else:
            # Key up
            self._pressed_keys.discard(vk)

        return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)


class HotkeyManager:
    """Drop-in replacement for the old RegisterHotKey-based manager.

    Uses LowLevelHotkey internally. Same start/stop API.
    """

    def __init__(self):
        self._hotkey = LowLevelHotkey()
        self._thread: Optional[threading.Thread] = None

    def start(self, callback: Callable[[], None]):
        if self._thread and self._thread.is_alive():
            return

        def _run():
            self._hotkey.start(callback)

        self._thread = threading.Thread(target=_run, daemon=True, name="hotkey-thread")
        self._thread.start()
        logger.info("Hotkey listener started (Ctrl+Shift+F12 via keyboard hook)")

    def stop(self):
        self._hotkey.stop()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Hotkey listener stopped")
