"""
System Tray & Global Hotkey Manager for Bahubali Desktop Buddy.

Lets Bahubali live in the Windows system tray (notification area) and be
summoned/dismissed with a global hotkey (Ctrl+Alt+B) from anywhere — even
when the desktop window is hidden. Right-click the tray icon for quick actions.

Optional dependencies (install with pip if missing):
    pip install pystray pynput pillow
"""

import os
import sys
import threading
import subprocess
import webbrowser

try:
    import pystray
    from PIL import Image, ImageDraw
    _PYSTRAY_AVAILABLE = True
except Exception:
    _PYSTRAY_AVAILABLE = False

try:
    from pynput import keyboard
    _PYNPUT_AVAILABLE = True
except Exception:
    _PYNPUT_AVAILABLE = False


class TrayManager:
    """Manages the system tray icon and global hotkey for Bahubali."""

    def __init__(self, gui_ref=None, ipc_port=18899):
        self.gui = gui_ref
        self.icon = None
        self.hotkey_listener = None
        self._running = False
        self.hotkey_combo = {
            keyboard.Key.ctrl_l,
            keyboard.Key.alt_l,
            keyboard.KeyCode(char="b"),
        } if _PYNPUT_AVAILABLE else None
        self._current_keys = set()

    # ── Icon image ──────────────────────────────────────────────────────────

    def _create_icon_image(self):
        """Draw a simple Bahubali-style tray icon (gold crown/sword on dark bg)."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Crown shape
        d.polygon(
            [(16, 48), (22, 24), (28, 40), (32, 22), (36, 40), (42, 24), (48, 48)],
            fill=(248, 196, 42, 255),  # royal gold
            outline=(28, 20, 15, 255),
            width=2,
        )
        # Ruby jewel in center
        d.ellipse((30, 30, 34, 34), fill=(215, 20, 45, 255))
        # Sword hilt below
        d.rectangle((29, 44, 35, 52), fill=(242, 192, 40, 255))
        d.rectangle((31, 48, 33, 56), fill=(150, 162, 178, 255))
        return img

    def _fallback_icon_path(self):
        """Use an existing sprite PNG if pystray/PIL aren't available."""
        assets = os.path.join(os.path.dirname(__file__), "assets", "celebrate_0.png")
        return assets if os.path.exists(assets) else None

    # ── Hotkey ──────────────────────────────────────────────────────────────

    def _on_key_press(self, key):
        if not _PYNPUT_AVAILABLE:
            return
        self._current_keys.add(key)
        if self.hotkey_combo and all(k in self._current_keys for k in self.hotkey_combo):
            self._toggle_gui()

    def _on_key_release(self, key):
        if not _PYNPUT_AVAILABLE:
            return
        self._current_keys.discard(key)

    def _toggle_gui(self):
        """Show or hide the Bahubali GUI window."""
        if not self.gui:
            return
        try:
            state = self.gui.root.state()
            if state == "normal" or state == "zoomed":
                self.gui.root.after(0, self.gui.root.withdraw)
            else:
                self.gui.root.after(0, self.gui.root.deiconify)
                self.gui.root.after(10, self.gui.root.focus_force)
        except Exception as e:
            print(f"[Tray toggle error] {e}")

    def _start_hotkey_listener(self):
        if not _PYNPUT_AVAILABLE:
            print("[Tray] pynput not installed — global hotkey disabled. Run: pip install pynput")
            return
        self.hotkey_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self.hotkey_listener.start()
        print("[Tray] Global hotkey active: Ctrl+Alt+B toggles Bahubali")

    # ── Tray menu actions ──────────────────────────────────────────────────

    def _menu_show(self, icon, item):
        if self.gui:
            self.gui.root.after(0, self.gui.root.deiconify)
            self.gui.root.after(10, self.gui.root.focus_force)

    def _menu_hide(self, icon, item):
        if self.gui:
            self.gui.root.after(0, self.gui.root.withdraw)

    def _menu_toggle(self, icon, item):
        self._toggle_gui()

    def _menu_say(self, icon, item):
        if self.gui:
            self.gui.root.after(0, lambda: self.gui.say("Jai Mahishmati! I am here at your service!", state="celebrate"))

    def _menu_status(self, icon, item):
        if self.gui:
            self.gui.root.after(0, lambda: self.gui.say("Bahubali is online and standing guard!", state="talk"))

    def _menu_quit(self, icon, item):
        self.stop()
        if self.gui:
            self.gui.root.after(0, self.gui.exit_app)

    # ── Start / Stop ───────────────────────────────────────────────────────

    def start(self):
        """Launch tray icon (background thread) and global hotkey listener."""
        self._running = True

        # Global hotkey (runs in its own daemon thread via pynput)
        self._start_hotkey_listener()

        # Tray icon (blocks, so run in background thread)
        if _PYSTRAY_AVAILABLE:
            image = self._create_icon_image()
            menu = pystray.Menu(
                pystray.MenuItem("Show Bahubali", self._menu_show),
                pystray.MenuItem("Hide Bahubali", self._menu_hide),
                pystray.MenuItem("Toggle (Ctrl+Alt+B)", self._menu_toggle, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Speak: Jai Mahishmati!", self._menu_say),
                pystray.MenuItem("Status", self._menu_status),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit Bahubali", self._menu_quit),
            )
            self.icon = pystray.Icon("bahubali", image, "Bahubali — Desktop Companion", menu)
            threading.Thread(target=self.icon.run, daemon=True).start()
            print("[Tray] System tray icon active (right-click for menu)")
        else:
            print("[Tray] pystray not installed — tray icon disabled. Run: pip install pystray pillow")

    def stop(self):
        """Stop tray icon and hotkey listener."""
        self._running = False
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
