"""Text injection into active applications using Windows APIs.

Two strategies:
  1. Clipboard paste (default) — works with 99% of apps
  2. SendInput typing — for apps that intercept Ctrl+V
"""
import ctypes
import logging
import time
from ctypes import wintypes

import win32api
import win32clipboard
import win32con

logger = logging.getLogger(__name__)


def paste_via_clipboard(text: str, restore_clipboard: bool = True):
    """Paste text using Ctrl+V (clipboard method).

    Works with virtually any Windows application.

    Args:
        text: The text to paste.
        restore_clipboard: If True, restores the previous clipboard content.
    """
    if not text:
        return

    # Save current clipboard content
    old_data = ""
    if restore_clipboard:
        try:
            win32clipboard.OpenClipboard()
            try:
                old_data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            except Exception:
                old_data = ""
        except Exception:
            pass
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    # Set our text to clipboard
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

    # Small delay for clipboard to settle
    time.sleep(0.05)

    # Send Ctrl+V
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord("V"), 0, 0, 0)
    time.sleep(0.03)
    win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    logger.info("Pasted %d chars via clipboard", len(text))

    # Restore old clipboard
    if restore_clipboard and old_data:
        time.sleep(0.15)
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(old_data, win32con.CF_UNICODETEXT)
        except Exception:
            pass
        finally:
            win32clipboard.CloseClipboard()


# ── SendInput (Unicode typing) for stubborn apps ──────────────────────

# Windows SendInput structures
INPUT_KEYBOARD = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ki", KEYBDINPUT),
    ]


KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


def type_via_sendinput(text: str, delay: float = 0.003):
    """Type text character-by-character using SendInput (Unicode).

    Use this for applications that intercept or block Ctrl+V.
    Slightly slower but works everywhere.

    Args:
        text: Text to type.
        delay: Delay between keystrokes in seconds (default: 3ms).
    """
    if not text:
        return

    for char in text:
        # Key down (Unicode)
        inp = INPUT(
            INPUT_KEYBOARD,
            KEYBDINPUT(0, ord(char), KEYEVENTF_UNICODE, 0, None),
        )
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        # Key up
        inp.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        time.sleep(delay)

    logger.info("Typed %d chars via SendInput", len(text))


def inject_text(text: str, method: str = "clipboard"):
    """Inject text into the currently focused application.

    Args:
        text: The text to inject.
        method: 'clipboard' (default, fast) or 'sendinput' (slower, universal).
    """
    if method == "sendinput":
        type_via_sendinput(text)
    else:
        paste_via_clipboard(text)
