"""
Computer Automation & System Controls for Bahubali — The Arms of Mahishmati.
Launches ANY installed app (UWP, Win32, Store, Steam, EXE) via smart search.
- Dynamically queries Windows Start Menu (Get-StartApps) for real AppIDs
- Falls back to PATH search, known aliases, then Start menu shell
- Volume & media controls, screenshots, clipboard, system stats
"""

import os
import re
import sys
import json
import ctypes
import datetime
import webbrowser
import subprocess
import psutil
from PIL import ImageGrab

# ── Windows Virtual Key Codes ──────────────────────────────────────────────────
VK_VOLUME_MUTE      = 0xAD
VK_VOLUME_DOWN      = 0xAE
VK_VOLUME_UP        = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP       = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

# ── Static alias table (common spoken names → Win32 commands) ─────────────────
STATIC_APP_ALIASES = {
    # Browsers (intentionally NOT in static aliases — they live in Program Files,
# not PATH. Resolved via _find_browser_exe() in open_app Strategy 1b.)
    # Dev tools
    "vscode":           "code",
    "vs code":          "code",
    "visual studio code": "code",
    "terminal":         "wt",
    "windows terminal": "wt",
    "cmd":              "cmd",
    "command prompt":   "cmd",
    "powershell":       "powershell",
    "git bash":         "bash",
    "notepad":          "notepad",
    "notepad++":        "notepad++",
    # System
    "explorer":         "explorer",
    "file explorer":    "explorer",
    "files":            "explorer",
    "calculator":       "calc",
    "calc":             "calc",
    "paint":            "mspaint",
    "task manager":     "taskmgr",
    "taskmgr":          "taskmgr",
    "settings":         "ms-settings:",   # will use start ms-settings:
    "control panel":    "control",
    # Media / Entertainment
    "vlc":              "vlc",
    "wmplayer":         "wmplayer",
    "windows media player": "wmplayer",
    "spotify":          "spotify",
    # "apple music" intentionally NOT in static aliases —
    # it's resolved dynamically via Start Menu AppID for reliable launching
    # Office
    "word":             "winword",
    "excel":            "excel",
    "powerpoint":       "powerpnt",
    "outlook":          "outlook",
    "onenote":          "onenote",
    # Messaging
    "whatsapp":         "whatsapp",
    "whats app":        "whatsapp",
    # Misc
    "steam":            "steam",
    "discord":          "discord",
    "zoom":             "zoom",
    "slack":            "slack",
    "teams":            "teams",
    "skype":            "skype",
    "obs":              "obs64",
}

# ── Cached Start-menu app list ─────────────────────────────────────────────────
_start_apps_cache = None


def _get_start_apps():
    """Fetch all installed apps from Windows Start Menu (cached)."""
    global _start_apps_cache
    if _start_apps_cache is not None:
        return _start_apps_cache
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            apps = json.loads(result.stdout.strip())
            if isinstance(apps, dict):
                apps = [apps]
            _start_apps_cache = apps
            return apps
    except Exception:
        pass
    return []


# Spoken aliases → their actual Start Menu display names. These prevent short
# names such as "code" from matching an unrelated app that contains "Code".
START_MENU_NAME_ALIASES = {
    "chrome": "google chrome",
    "google chrome": "google chrome",
    "edge": "microsoft edge",
    "msedge": "microsoft edge",
    "code": "visual studio code",
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "visual studio code": "visual studio code",
    "calc": "calculator",
    "taskmgr": "task manager",
    "files": "file explorer",
    "explorer": "file explorer",
    "file explorer": "file explorer",
    "cmd": "command prompt",
    "command prompt": "command prompt",
    "powershell": "windows powershell",
    "whats app": "whatsapp",
}


def _find_app_in_startmenu(query):
    """
    Match a spoken name against Get-StartApps. Returns (name, appid).
    Deliberately avoids one-word fuzzy matches, which could launch an unrelated
    app (for example "spotify music" must never resolve to "Apple Music").
    """
    apps = _get_start_apps()
    q = (query or "").lower().strip()
    if not q:
        return None, None

    best = None
    best_rank = None
    for app in apps:
        name = (app.get("Name") or "").strip()
        appid = app.get("AppID") or ""
        if not name or not appid:
            continue
        normalized = name.lower()
        if normalized == q:
            score = 100
        elif normalized.startswith(q):
            score = 90
        elif q in normalized:
            score = 80
        elif len(normalized) >= 4 and normalized in q:
            score = 70
        else:
            continue
        # Prefer the closer match, then the shorter/more canonical app name
        # (e.g. "WhatsApp" over "WhatsApp Beta").
        rank = (-score, len(normalized), normalized)
        if best_rank is None or rank < best_rank:
            best = (name, appid)
            best_rank = rank

    return best if best else (None, None)


def _find_chrome_exe():
    """Search common Chrome installation paths on Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _find_browser_exe(browser_name):
    """Find common browser executables by name."""
    browser_paths = {
        "chrome": _find_chrome_exe(),
        "google chrome": _find_chrome_exe(),
        "msedge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        ],
        "microsoft edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe"),
        ],
        "opera": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"),
            r"C:\Program Files\Opera\opera.exe",
        ],
        "brave": [
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
    }
    paths = browser_paths.get(browser_name.lower())
    if paths is None:
        return None
    if isinstance(paths, str):
        return paths if os.path.exists(paths) else None
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def _find_common_app_exe(app_name):
    """Find common Windows app executables by name in standard install locations."""
    app_paths = {
        "discord": [
            os.path.expandvars(r"%LOCALAPPDATA%\Discord\app-*\Discord.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Discord\Discord.exe"),
        ],
        "spotify": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
            r"C:\Program Files\WindowsApps\Spotify.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Spotify\Spotify.exe"),
        ],
        "steam": [
            r"C:\Program Files (x86)\Steam\Steam.exe",
            r"C:\Program Files\Steam\Steam.exe",
        ],
        "whatsapp": [
            os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"),
        ],
        "zoom": [
            os.path.expandvars(r"%APPDATA%\Zoom\bin\Zoom.exe"),
        ],
        "slack": [
            os.path.expandvars(r"%LOCALAPPDATA%\slack\slack.exe"),
        ],
        "teams": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Teams\Teams.exe"),
        ],
        "skype": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Skype\Skype.exe"),
            r"C:\Program Files (x86)\Microsoft\Skype for Desktop\Skype.exe",
        ],
        "obs": [
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        ],
        "notepad++": [
            r"C:\Program Files\Notepad++\notepad++.exe",
            r"C:\Program Files (x86)\Notepad++\notepad++.exe",
        ],
        "vlc": [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        ],
        "paint": [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "mspaint.exe"),
        ],
        "calculator": [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "calc.exe"),
        ],
        "notepad": [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "notepad.exe"),
        ],
        "taskmgr": [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "taskmgr.exe"),
        ],
    }
    paths = app_paths.get(app_name.lower())
    if not paths:
        return None
    import glob as _glob
    for pattern in paths:
        matches = _glob.glob(pattern)
        for p in matches:
            if os.path.exists(p):
                return p
    return None


def _find_app_exe_everywhere(app_name):
    """
    Generic fallback: search common Windows install directories for any .exe
    matching the app name. Covers apps not in the predefined maps.
    """
    import glob as _glob

    base_dirs = [
        os.path.expandvars(r"%PROGRAMFILES%"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
        os.path.expandvars(r"%LOCALAPPDATA%"),
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32"),
    ]

    # Candidate executable names
    candidates = [
        f"{app_name}.exe",
        f"{app_name.lower()}.exe",
        f"{app_name.title()}.exe",
        f"{app_name.capitalize()}.exe",
    ]

    for base in base_dirs:
        if not os.path.isdir(base):
            continue
        for candidate in candidates:
            # Direct file in base dir
            path = os.path.join(base, candidate)
            if os.path.exists(path):
                return path
            # Inside a subdirectory named after the app (e.g. Discord\app-xxx\Discord.exe)
            for depth in range(1, 4):
                pattern = os.path.join(base, "*" * depth, candidate)
                matches = _glob.glob(pattern)
                for p in matches:
                    if os.path.exists(p) and app_name.lower() in p.lower():
                        return p
            # Inside an app-named subdirectory
            subdir = os.path.join(base, app_name)
            if os.path.isdir(subdir):
                path = os.path.join(subdir, candidate)
                if os.path.exists(path):
                    return path
    return None


def _start_menu_dirs():
    """Standard Start Menu shortcut folders (user + all-users)."""
    return [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]


def _find_start_menu_shortcut(app_name):
    """
    Find a .lnk shortcut in the Start Menu folders matching app_name.
    This is the most reliable way to launch Win32 apps whose Get-StartApps
    AppID is an opaque 'Microsoft.AutoGenerated.{GUID}' token.
    """
    import glob as _glob

    q = (app_name or "").lower().strip()
    if not q:
        return None

    shortcuts = []
    for base in _start_menu_dirs():
        if not os.path.isdir(base):
            continue
        try:
            shortcuts.extend(_glob.glob(os.path.join(base, "**", "*.lnk"), recursive=True))
        except Exception:
            continue

    if not shortcuts:
        return None

    def _score(path):
        stem = os.path.splitext(os.path.basename(path))[0].lower()
        if stem == q:
            return 4
        if stem.startswith(q):
            return 3
        if q in stem:
            return 2
        if stem in q:
            return 1
        return 0

    scored = [(s, p) for s, p in ((_score(p), p) for p in shortcuts) if s > 0]
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    return scored[0][1]


def _visible_windows():
    """Return [(pid, title)] for visible top-level windows."""
    import ctypes
    from ctypes import wintypes

    results = []
    try:
        user32 = ctypes.windll.user32
        proc_type = ctypes.WINFUNCTYPE(
            ctypes.c_bool, wintypes.HWND, wintypes.LPARAM
        )

        def _callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                results.append((pid.value, buf.value))
            return True

        user32.EnumWindows(proc_type(_callback), 0)
    except Exception:
        pass
    return results


def _app_tokens(app_name):
    """Significant lowercase tokens for an app name ('Google Chrome' -> chrome, google)."""
    noise = {"app", "apps", "application", "the", "microsoft", "windows", "desktop", "player"}
    raw = re.split(r"[^a-z0-9]+", (app_name or "").lower())
    return [t for t in raw if len(t) > 2 and t not in noise]


def _name_matches(candidate, app_name):
    """True when a process name or window title plausibly belongs to app_name."""
    tokens = _app_tokens(app_name)
    if not tokens:
        return False
    cand = re.sub(r"[^a-z0-9]", "", (candidate or "").lower())
    if not cand:
        return False
    return any(token in cand for token in tokens)


def _app_is_running_with_window(app_name):
    """True when a visible window belongs to the given app."""
    pids = {}
    for pid, title in _visible_windows():
        if _name_matches(title, app_name):
            return True
        pids.setdefault(pid, []).append(title)
    if not pids:
        return False
    for pid in pids:
        try:
            import psutil
            proc_name = psutil.Process(pid).name()
        except Exception:
            continue
        if _name_matches(proc_name, app_name):
            return True
    return False


def _focus_existing_window(app_name):
    """Bring an already-running app's window to the foreground. True if found."""
    import ctypes
    from ctypes import wintypes

    targets = []
    for pid, title in _visible_windows():
        if _name_matches(title, app_name):
            targets.append(pid)
    if not targets:
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if _name_matches(proc.info.get('name') or "", app_name):
                    pid = proc.info.get('pid')
                    for wpid, _title in _visible_windows():
                        if wpid == pid:
                            targets.append(pid)
        except Exception:
            pass
    if not targets:
        return False

    try:
        user32 = ctypes.windll.user32
        proc_type = ctypes.WINFUNCTYPE(
            ctypes.c_bool, wintypes.HWND, wintypes.LPARAM
        )

        def _callback(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in targets:
                    user32.ShowWindow(hwnd, 9)   # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
                    return False
            return True

        user32.EnumWindows(proc_type(_callback), 0)
    except Exception:
        pass
    return True


def _package_install_location(appid):
    """Install folder of the Store/UWP package behind an AppID, if installed."""
    pfn = (appid or "").split("!")[0].strip()
    if not pfn or "." not in pfn:
        return None
    ps = (
        "Get-AppxPackage | Where-Object { $_.PackageFamilyName -eq '" + pfn + "' -or "
        "$_.PackageFamilyName -like '" + pfn + "*' } | "
        "Select-Object -First 1 -ExpandProperty InstallLocation"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=20
        )
        loc = (result.stdout or "").strip().splitlines()
        if loc and loc[0] and os.path.isdir(loc[0]):
            return loc[0]
    except Exception:
        pass
    return None


def _package_main_exe(appid, app_name):
    """Find the main executable of a Store app package (e.g. WhatsApp.Root.exe)."""
    loc = _package_install_location(appid)
    if not loc:
        return None

    import glob as _glob
    try:
        exes = _glob.glob(os.path.join(loc, "*.exe"))
    except Exception:
        exes = []
    if not exes:
        return None

    helpers = {
        "createdump.exe", "defaults.exe", "appdefaults.exe", "restartagent.exe",
        "sharedhelper.exe", "amplibraryagent.exe", "wmfcapabilities.exe",
        "crashpad_handler.exe", "vcredist_x86.exe", "vcredist_x64.exe",
    }
    candidates = [e for e in exes if os.path.basename(e).lower() not in helpers]
    if not candidates:
        candidates = exes

    tokens = _app_tokens(app_name)
    for exe in candidates:
        stem = os.path.splitext(os.path.basename(exe))[0].lower()
        if any(token in stem for token in tokens):
            return exe
    # Fall back to the largest executable (the real app is usually the biggest).
    try:
        return max(candidates, key=lambda p: os.path.getsize(p))
    except Exception:
        return candidates[0]


def _launch_shell_appid(appid, app_name="", wait=8.0):
    """
    Launch a Store/UWP app by AppID and confirm it actually opened.

    PowerShell's Start-Process is used instead of explorer.exe: explorer
    exits with code 1 even on success and can terminate a running instance.
    Success is confirmed by observing a real window.
    """
    import time as _time

    # If it is already open, just bring it forward instead of relaunching.
    if app_name and _app_is_running_with_window(app_name):
        if _focus_existing_window(app_name):
            return True

    ps_cmd = 'Start-Process "shell:AppsFolder' + chr(92) + str(appid) + '"'
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=25
        )
        if result.returncode != 0:
            return False
    except Exception:
        return False

    if not app_name:
        return True

    deadline = _time.time() + wait
    while _time.time() < deadline:
        if _app_is_running_with_window(app_name):
            return True
        _time.sleep(0.5)
    return False


def _launch_appid(appid, app_name=""):
    """
    Launch an app using its Windows AppID (UWP, Win32, shortcuts, URIs).
    Tries every viable mechanism and only reports success when one is accepted
    by the OS, so callers can fall through to the next strategy on failure.
    """
    if not appid:
        return False

    # Web / protocol handlers
    if appid.startswith(("http://", "https://")):
        webbrowser.open(appid)
        return True

    if "://" in appid:  # steam://, spotify:, etc.
        try:
            os.startfile(appid)
            return True
        except Exception:
            try:
                subprocess.Popen(f'start "" "{appid}"', shell=True)
                return True
            except Exception:
                return False

    # Win32 EXE paths: "{GUID}\\path\\app.exe", "C:\\path\\app.exe", or "Name.exe"
    if appid.lower().endswith((".exe", ".lnk", ".msc", ".cpl", ".bat", ".cmd")) or "\\" in appid:
        # Strip a leading {GUID}\ prefix and any known install-root GUID prefix
        exe_path = re.sub(r"^\{[^}]+\}\\", "", appid)
        if not os.path.isabs(exe_path):
            # Relative to a standard install root (e.g. "Git\\cmd\\git-gui.exe")
            for root in (os.path.expandvars(r"%PROGRAMFILES%"),
                         os.path.expandvars(r"%PROGRAMFILES(X86)%"),
                         os.path.expandvars(r"%WINDIR%\\System32"),
                         os.path.expandvars(r"%LOCALAPPDATA%")):
                candidate = os.path.join(root, exe_path)
                if os.path.exists(candidate):
                    exe_path = candidate
                    break
        if os.path.isabs(exe_path) and os.path.exists(exe_path):
            if _launch_file(exe_path):
                return True
        # Not a resolvable path — fall through to shell/shortcut handling below.

    # Opaque auto-generated AppIDs resolve best through their actual shortcut
    if appid.startswith("Microsoft.AutoGenerated.") and app_name:
        shortcut = _find_start_menu_shortcut(app_name)
        if shortcut and _launch_file(shortcut):
            return True

    # Store/UWP apps and registered names ("Chrome", "MSEdge", "electron.app.X").
    # explorer.exe returns 1 even on success, so the window is what counts.
    if _launch_shell_appid(appid, app_name):
        return True

    # Store apps whose shell activation is blocked: run the package executable.
    if app_name:
        exe = _package_main_exe(appid, app_name)
        if exe and _launch_file(exe):
            import time as _time
            deadline = _time.time() + 8.0
            while _time.time() < deadline:
                if _app_is_running_with_window(app_name):
                    return True
                _time.sleep(0.5)
            # Process started even if no window appeared yet (tray-only apps).
            return True

    # Last resort: the Start Menu shortcut itself
    if app_name:
        shortcut = _find_start_menu_shortcut(app_name)
        if shortcut and _launch_file(shortcut):
            return True

    return False


def _launch_file(path):
    """Launch a file/exe/shortcut with os.startfile, falling back to Popen."""
    try:
        os.startfile(path)
        return True
    except Exception:
        pass
    try:
        subprocess.Popen(f'start "" "{path}"', shell=True)
        return True
    except Exception:
        return False


class SystemExecutor:
    def __init__(self):
        self.user_dir = os.path.expanduser("~")

    def press_key(self, vk_code, times=1):
        """Simulate a Windows virtual key press."""
        for _ in range(times):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

    # ── Volume ────────────────────────────────────────────────────────────────

    def change_volume(self, action="up", amount=5):
        if action == "mute":
            self.press_key(VK_VOLUME_MUTE)
            return True, "Toggled mute, O brave one!"
        elif action == "up":
            self.press_key(VK_VOLUME_UP, times=max(1, amount // 2))
            return True, "Volume raised!"
        elif action == "down":
            self.press_key(VK_VOLUME_DOWN, times=max(1, amount // 2))
            return True, "Volume lowered!"
        return False, "Unknown volume action."

    # ── Media ─────────────────────────────────────────────────────────────────

    def media_control(self, action="play_pause"):
        actions = {
            "play_pause": VK_MEDIA_PLAY_PAUSE,
            "next":       VK_MEDIA_NEXT_TRACK,
            "prev":       VK_MEDIA_PREV_TRACK,
            "stop":       VK_MEDIA_STOP,
        }
        vk = actions.get(action)
        if vk:
            self.press_key(vk)
            return True, f"Media {action} triggered!"
        return False, "Unknown media action."

    def _find_apple_music_appid(self):
        """Dynamically find the Apple Music AppID from the Start Menu."""
        apps = _get_start_apps()
        for app in apps:
            name = app.get("Name", "").lower()
            appid = app.get("AppID", "")
            if "apple music" in name or "applemusic" in name:
                return appid
        return None

    def _activate_apple_music_window(self):
        """Use PowerShell to find and bring the Apple Music window to the foreground."""
        ps_cmd = '''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
$proc = Get-Process -Name "AppleMusic" -ErrorAction SilentlyContinue
if ($proc) {
    foreach ($p in $proc) {
        if ($p.MainWindowHandle -ne [IntPtr]::Zero) {
            [Win32]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
            [Win32]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
        }
    }
}
'''
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5
            )
        except Exception:
            pass

    def _send_media_play_key(self):
        """Send media play/pause exactly once via the most reliable method available.

        play/pause is a toggle, so we deliberately fire it only a single time —
        firing it repeatedly (shell + ctypes + retries) would play then pause
        the track and leave the song silent.
        """
        # WScript.Shell SendKeys routes media keys to the active audio session.
        ps_cmd = '$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys([char]0xB3)'
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5
            )
            return
        except Exception:
            pass
        # Fallback: ctypes virtual key press (only if the shell method failed)
        try:
            self.press_key(VK_MEDIA_PLAY_PAUSE)
        except Exception:
            pass

    def _click_apple_music_play_button(self):
        """Try to click the Apple Music play button area via pyautogui."""
        try:
            import pyautogui
            import time as _time
            pyautogui.FAILSAFE = False
            screen_w, screen_h = pyautogui.size()
            # Apple Music play button is typically near the top-center of the window
            # Try a few common play button positions
            candidates = [
                (int(screen_w * 0.5), int(screen_h * 0.30)),   # center-ish
                (int(screen_w * 0.5), int(screen_h * 0.25)),   # upper center
            ]
            for x, y in candidates:
                try:
                    pyautogui.click(x, y)
                    _time.sleep(0.3)
                except Exception:
                    pass
        except Exception:
            pass

    def _apple_music_native_installed(self):
        """Check if the Apple Music desktop app is actually installed (not just web)."""
        try:
            for p in psutil.process_iter(['name']):
                if "applemusic" in p.name().lower():
                    return True
        except Exception:
            pass
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-StartApps | Where-Object {$_.Name -like '*Apple Music*'} | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
        except Exception:
            pass
        return False

    def _play_music_apple_music_native(self, clean):
        """
        Launch Apple Music native app with a musics:// URI and trigger playback once.
        Returns (success, msg). Only call when the native app is confirmed installed.
        """
        import urllib.parse
        import threading
        import time
        import requests

        track_name = None
        artist_name = None
        play_uri = None

        # Query iTunes Store API for the exact track
        for country in ['in', 'us']:
            try:
                resp = requests.get(
                    'https://itunes.apple.com/search',
                    params={'term': clean, 'country': country, 'media': 'music', 'limit': 1},
                    timeout=3.5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('resultCount', 0) > 0:
                        track = data['results'][0]
                        track_name = track.get('trackName', clean)
                        artist_name = track.get('artistName', '')
                        url = track.get('trackViewUrl', '')
                        if url:
                            play_uri = url.replace('https://', 'musics://')
                            if 'action=play' not in play_uri:
                                play_uri += '&action=play'
                            break
            except Exception:
                pass

        if not play_uri:
            encoded = urllib.parse.quote(clean)
            play_uri = f"musics://music.apple.com/search?term={encoded}&action=play"
            display_title = f"'{clean}'"
        else:
            display_title = f"'{track_name}' by {artist_name}" if artist_name else f"'{track_name}'"

        try:
            subprocess.Popen(f'cmd.exe /c start "" "{play_uri}"', shell=True)

            def _ensure_playing():
                import time as _time

                # Wait for the Apple Music process to actually start (up to ~12s)
                running = False
                for _ in range(12):
                    try:
                        running = any(
                            "applemusic" in p.name().lower()
                            for p in psutil.process_iter(['name'])
                        )
                    except Exception:
                        running = False
                    if running:
                        break
                    _time.sleep(1.0)

                if not running:
                    return  # Native app didn't start — nothing to do

                # Focus the window so the media key reaches Apple Music
                self._activate_apple_music_window()
                _time.sleep(1.0)

                # play/pause is a toggle — fire it exactly once
                self._send_media_play_key()

            threading.Thread(target=_ensure_playing, daemon=True).start()
            return True, f"⚔️ Playing {display_title} in Apple Music! Enjoy the victory anthem, Commander!"
        except Exception as e:
            return False, f"Apple Music launch failed: {e}"

    def play_music(self, song_or_artist="", service="apple_music"):
        """
        Play music with a fallback chain that actually plays audio:

        1. Local music files (plays directly via default media player — most reliable)
        2. Apple Music native app (musics:// URI + media key, only if installed)
        3. Spotify desktop app (opens search in Spotify app)
        4. YouTube web search (opens browser — user taps play)

        Never presses Space or media keys on web pages.
        """
        import urllib.parse
        import time

        clean = (song_or_artist or "").strip()
        clean = re.sub(r'\b(in|on)\s+apple\s+music\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\b(songs?|tracks?|music)\b', '', clean, flags=re.IGNORECASE).strip()

        if not clean:
            # No song specified: resume playback
            if self._apple_music_native_installed():
                self._activate_apple_music_window()
                time.sleep(0.5)
                self._send_media_play_key()
                return True, "Resuming your royal melodies in Apple Music!"
            return self.play_local_music("")

        # ── 1. Local music files (actually plays audio — no key presses needed) ──
        success, msg = self.play_local_music(clean)
        if success:
            return True, msg

        # ── 2. Apple Music native app (only if actually installed) ─────────────
        if service == "apple_music" and self._apple_music_native_installed():
            success, msg = self._play_music_apple_music_native(clean)
            if success:
                return True, msg

        # ── 3. Spotify desktop app ─────────────────────────────────────────────
        encoded = urllib.parse.quote(clean)
        try:
            spotify_uri = f"spotify:search:{encoded}"
            subprocess.Popen(f'start "" "{spotify_uri}"', shell=True)
            return True, f"⚔️ Searching Spotify for '{clean}'! Open Spotify and tap play, Commander!"
        except Exception:
            pass

        # ── 4. YouTube web search (last resort — no keys pressed) ──────────────
        yt_url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(yt_url)
        return True, f"⚔️ Opened YouTube search for '{clean}' — tap play on the result, Commander!"

    # ── Spotify Playback ────────────────────────────────────────────────────

    def play_spotify(self, song_or_artist=""):
        """
        Play a song or artist on Spotify via the spotify:// URI scheme.
        Falls back to the Spotify web player if the desktop app isn't handling it.
        """
        import urllib.parse
        clean = (song_or_artist or "").strip()

        if not clean:
            # Just open/resume Spotify
            try:
                subprocess.Popen('start "" "spotify:"', shell=True)
                return True, "Opening Spotify, Commander!"
            except Exception as e:
                webbrowser.open("https://open.spotify.com")
                return True, f"Opened Spotify web player! ({e})"

        encoded = urllib.parse.quote(clean)
        # Try the Spotify search URI first
        spotify_uri = f"spotify:search:{encoded}"
        try:
            subprocess.Popen(f'start "" "{spotify_uri}"', shell=True)
            return True, f"⚔️ Searching Spotify for '{clean}'! Let the battle anthem begin!"
        except Exception:
            # Fallback to web player
            web_url = f"https://open.spotify.com/search/{encoded}"
            webbrowser.open(web_url)
            return True, f"Opened Spotify web search for '{clean}'!"

    # ── Local Music Playback ────────────────────────────────────────────────

    def play_local_music(self, song_name=""):
        """
        Play a local music file from the user's Music folder.
        Searches for MP3/WAV/M4A files matching the name.
        """
        import glob
        music_dirs = [
            os.path.join(self.user_dir, "Music"),
            os.path.join(self.user_dir, "Desktop"),
        ]
        extensions = ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.aac", "*.wma")

        matches = []
        for mdir in music_dirs:
            if not os.path.isdir(mdir):
                continue
            for ext in extensions:
                matches.extend(glob.glob(os.path.join(mdir, "**", ext), recursive=True))

        if not matches:
            return False, "No local music files found in your Music folder, Commander."

        if song_name:
            q = song_name.lower()
            scored = []
            for path in matches:
                name = os.path.basename(path).lower()
                score = 0
                if q in name:
                    score += 2
                if name.startswith(q):
                    score += 3
                if q == os.path.splitext(name)[0]:
                    score += 5
                if score > 0:
                    scored.append((score, path))
            scored.sort(reverse=True, key=lambda x: x[0])
            if scored:
                best = scored[0][1]
            else:
                best = matches[0]
        else:
            best = matches[0]

        try:
            subprocess.Popen(f'start "" "{best}"', shell=True)
            return True, f"⚔️ Playing {os.path.basename(best)} from your vault, Commander!"
        except Exception as e:
            return False, f"Could not play local music: {e}"

    # ── Brightness Control ──────────────────────────────────────────────────

    def set_brightness(self, level):
        """
        Set screen brightness (0-100) via PowerShell WMI.
        """
        try:
            level = int(level)
            if level < 0 or level > 100:
                return False, "Brightness must be between 0 and 100."
            ps_cmd = (
                f'$brightness = {level}; '
                '$monitors = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods; '
                'foreach ($m in $monitors) { $m.WmiSetBrightness(1, $brightness) }'
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=10
            )
            return True, f"Brightness set to {level}%, Commander."
        except Exception as e:
            return False, f"Could not set brightness: {e}"

    def get_brightness(self):
        """Get current screen brightness via PowerShell WMI."""
        try:
            ps_cmd = (
                'Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | '
                'Select-Object -ExpandProperty CurrentBrightness'
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=10
            )
            if res.returncode == 0 and res.stdout.strip():
                level = int(res.stdout.strip().split()[0])
                return True, f"Current brightness: {level}%"
            return False, "Could not read brightness."
        except Exception as e:
            return False, f"Could not read brightness: {e}"

    # ── Windows Toast Notifications ─────────────────────────────────────────

    def show_toast(self, title, message, duration=5):
        """
        Show a Windows 10/11 toast notification via PowerShell (no extra packages).
        """
        ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTitle = "{title}"
$notify.BalloonTipText = "{message}"
$notify.Visible = $true
$notify.ShowBalloonTip({duration} * 1000)
Start-Sleep -Seconds {duration}
$notify.Dispose()
'''
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                capture_output=True, text=True, timeout=duration + 5
            )
            return True, "Toast notification sent."
        except Exception as e:
            return False, f"Toast failed: {e}"

    # ── Recycle Bin ─────────────────────────────────────────────────────────

    def empty_recycle_bin(self):
        """Empty the Windows Recycle Bin via PowerShell."""
        ps_cmd = 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=15
            )
            return True, "Recycle bin emptied — the vault is clean, Commander!"
        except Exception as e:
            return False, f"Could not empty recycle bin: {e}"

    # ── Process Control ─────────────────────────────────────────────────────

    def kill_process(self, process_name):
        """Kill a running process by name (e.g. 'chrome', 'notepad')."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", f"{process_name}.exe"],
                capture_output=True, text=True, timeout=10
            )
            return True, f"Process '{process_name}' terminated by royal decree."
        except Exception as e:
            return False, f"Could not kill '{process_name}': {e}"

    def list_running_processes(self, limit=12):
        """List top running processes by memory usage."""
        try:
            procs = []
            for p in psutil.process_iter(['name', 'memory_info', 'cpu_percent']):
                try:
                    info = p.info
                    mem_mb = (info['memory_info'].rss or 0) / (1024 * 1024)
                    procs.append((info['name'], round(mem_mb, 1)))
                except Exception:
                    continue
            procs.sort(key=lambda x: x[1], reverse=True)
            top = procs[:limit]
            lines = [f"• {name} — {mem} MB" for name, mem in top]
            return True, "Top processes:\n" + "\n".join(lines)
        except Exception as e:
            return False, f"Could not list processes: {e}"

    # ── Folder / File Operations ────────────────────────────────────────────

    def open_folder(self, folder_path=""):
        """Open a folder in Windows Explorer. Defaults to user profile."""
        target = folder_path or self.user_dir
        if not os.path.exists(target):
            return False, f"Folder not found: {target}"
        try:
            subprocess.Popen(f'explorer "{target}"', shell=True)
            return True, f"Opened {target}, Commander."
        except Exception as e:
            return False, f"Could not open folder: {e}"

    def create_note(self, title="", content=""):
        """
        Create a sticky note (text file) on the Desktop.
        """
        try:
            desktop = os.path.join(self.user_dir, "Desktop")
            os.makedirs(desktop, exist_ok=True)
            safe_title = "".join(c for c in (title or "Bahubali Note") if c.isalnum() or c in " -_").strip()
            if not safe_title:
                safe_title = "Bahubali Note"
            ts = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{ts}.txt"
            filepath = os.path.join(desktop, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content or "Bahubali note — Jai Mahishmati!\n")
            subprocess.Popen(f'notepad "{filepath}"', shell=True)
            return True, f"Note created: {filename} on your Desktop."
        except Exception as e:
            return False, f"Could not create note: {e}"

    # ── Weather ─────────────────────────────────────────────────────────────

    def get_weather(self, city=""):
        """
        Get current weather via wttr.in (free, no API key).
        """
        import urllib.request
        import urllib.parse
        try:
            query = urllib.parse.quote(city) if city else ""
            url = f"https://wttr.in/{query}?format=3" if city else "https://wttr.in?format=3"
            req = urllib.request.Request(url, headers={"User-Agent": "Bahubali-Buddy"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                weather = resp.read().decode("utf-8").strip()
            if weather:
                return True, weather
            return False, "Could not fetch weather, Commander."
        except Exception as e:
            return False, f"Weather error: {e}"

    # ── List & Open All Installed Apps ────────────────────────────────────────

    def list_all_apps(self, limit=50):
        """
        List all installed apps from the Windows Start Menu.
        Returns (success, message) with app names.
        """
        apps = _get_start_apps()
        if not apps:
            return False, "No installed apps found in Start Menu, Commander."

        app_names = sorted([a.get("Name", "Unknown") for a in apps])
        total = len(app_names)
        shown = app_names[:limit]
        lines = [f"• {name}" for name in shown]
        msg = f"Installed apps ({total} total, showing first {limit}):\n" + "\n".join(lines)
        if total > limit:
            msg += f"\n... and {total - limit} more. Say 'open <app name>' to launch any of them!"
        return True, msg

    def open_all_apps(self, limit=20):
        """
        Open all installed apps from the Start Menu (limited to avoid system overload).
        Returns (success, message).
        """
        apps = _get_start_apps()
        if not apps:
            return False, "No installed apps found to launch, Commander."

        app_list = sorted(apps, key=lambda a: a.get("Name", ""))
        launched = 0
        failed = 0

        for app in app_list[:limit]:
            appid = app.get("AppID", "")
            if not appid:
                failed += 1
                continue
            try:
                if appid.startswith("http://") or appid.startswith("https://"):
                    webbrowser.open(appid)
                    launched += 1
                elif appid.endswith(".exe") or "\\" in appid:
                    exe_path = re.sub(r"^\{[^}]+\}\\", "", appid)
                    if os.path.isabs(exe_path) and os.path.exists(exe_path):
                        if self._launch_exe(exe_path):
                            launched += 1
                        else:
                            failed += 1
                    else:
                        if self._launch_exe(appid):
                            launched += 1
                        else:
                            failed += 1
                else:
                    subprocess.Popen(
                        f'explorer.exe "shell:AppsFolder\\{appid}"',
                        shell=True
                    )
                    launched += 1
                import time as _time
                _time.sleep(0.3)  # Small delay to avoid overwhelming the system
            except Exception:
                failed += 1

        return True, f"⚔️ Launched {launched} apps! ({failed} failed). Jai Mahishmati!"

    # ── App Launcher (THE MAIN FIX) ───────────────────────────────────────────

    def _launch_exe(self, exe_path):
        """Try multiple methods to launch an executable. Returns True if any worked."""
        # Method 1: os.startfile (most reliable on Windows)
        try:
            os.startfile(exe_path)
            return True
        except Exception:
            pass
        # Method 2: subprocess.Popen directly with the exe
        try:
            subprocess.Popen([exe_path], shell=False)
            return True
        except Exception:
            pass
        # Method 3: start command via shell
        try:
            subprocess.Popen(f'start "" "{exe_path}"', shell=True)
            return True
        except Exception:
            pass
        return False

    def open_app(self, app_name):
        """
        Universal app launcher. The Windows Start Menu is tried first because
        it knows Store apps, desktop apps, and apps that are not on PATH.
        Aliases and executable searches are fallbacks, never silent dead ends.
        """
        name_lower = re.sub(r"\s+", " ", (app_name or "").lower()).strip()
        name_lower = re.sub(r"^(?:the\s+|my\s+)", "", name_lower)
        name_lower = re.sub(r"\s+(?:app|application|please)$", "", name_lower).strip()
        if not name_lower:
            return False, "Tell me which app to open, Commander."

        attempts = []
        alias = STATIC_APP_ALIASES.get(name_lower)
        canonical_name = START_MENU_NAME_ALIASES.get(name_lower)
        search_names = list(dict.fromkeys(
            q for q in (canonical_name, alias, name_lower) if q
        ))

        # ── Strategy 1: Start Menu (Store apps and desktop apps) ─────────────
        for search_name in search_names:
            found_name, found_appid = _find_app_in_startmenu(search_name)
            if found_appid:
                attempts.append(f"start menu: {found_name} ({found_appid})")
                if _launch_appid(found_appid, found_name):
                    return True, f"⚔️ Opening {found_name} for you, warrior!"

        # ── Strategy 2: Start Menu shortcut (.lnk), including aliases ────────
        for shortcut_query in search_names:
            if not shortcut_query or "\\" in shortcut_query or ":" in shortcut_query:
                continue
            shortcut = _find_start_menu_shortcut(shortcut_query)
            if shortcut:
                attempts.append(f"shortcut: {shortcut}")
                if _launch_file(shortcut):
                    return True, f"⚔️ Opening {app_name} for you, warrior!"

        # ── Strategy 3: Known browser and common app install paths ───────────
        for label, exe in (
            ("browser path", _find_browser_exe(name_lower)),
            ("common path", _find_common_app_exe(name_lower)),
        ):
            if exe:
                attempts.append(f"{label}: {exe}")
                if self._launch_exe(exe):
                    return True, f"⚔️ Opening {app_name} for you, warrior!"

        # ── Strategy 4: Static alias and protocol handlers ───────────────────
        if alias:
            attempts.append(f"alias: {alias}")
            if ":" in alias and "\\" not in alias:
                try:
                    os.startfile(alias)
                    return True, f"⚔️ Opening {app_name} for you, warrior!"
                except Exception:
                    pass
            elif alias.lower().endswith(".exe") or "\\" in alias:
                if self._launch_exe(alias):
                    return True, f"⚔️ Opening {app_name} for you, warrior!"
            else:
                # Check PATH first; do not claim success for a bare 'start name'.
                try:
                    result = subprocess.run(
                        ["where", alias], capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        exe = result.stdout.strip().splitlines()[0]
                        attempts.append(f"alias PATH: {exe}")
                        if self._launch_exe(exe):
                            return True, f"⚔️ Opening {app_name} for you, warrior!"
                except Exception:
                    pass

        # ── Strategy 5: Search PATH using the spoken name ────────────────────
        try:
            result = subprocess.run(
                ["where", name_lower], capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0 and result.stdout.strip():
                exe = result.stdout.strip().splitlines()[0]
                attempts.append(f"PATH: {exe}")
                if self._launch_exe(exe):
                    return True, f"⚔️ Opening {app_name} for you, warrior!"
        except Exception:
            pass

        # ── Strategy 6: Deep executable search (last resort, can be slow) ────
        generic_exe = _find_app_exe_everywhere(name_lower)
        if generic_exe:
            attempts.append(f"deep search: {generic_exe}")
            if self._launch_exe(generic_exe):
                return True, f"⚔️ Opening {app_name} for you, warrior!"

        detail = "\n".join(f"  • {a}" for a in attempts) or "  • No installed app matched that name"
        return False, (
            f"Could not open '{app_name}'. Try its Start Menu name, or say 'list apps'.\n"
            f"Tried:\n{detail}"
        )

    def open_vscode(self, path=None):
        """Open VS Code at a path."""
        target = path or os.getcwd()
        try:
            subprocess.Popen(["code", target])
            return True, f"Opened VS Code at {target}"
        except Exception as e:
            return False, f"Could not open VS Code: {e}"

    # ── Web / Search ──────────────────────────────────────────────────────────

    def open_url_or_search(self, target, is_search=False):
        if is_search or not (target.startswith("http://") or target.startswith("https://")):
            if not target.startswith("http"):
                url = f"https://www.google.com/search?q={target.replace(' ', '+')}"
            else:
                url = target
        else:
            url = target
        webbrowser.open(url)
        return True, f"Opened: {url}"

    def search_youtube(self, query):
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return True, f"Searching YouTube for '{query}'"

    def open_youtube(self):
        webbrowser.open("https://www.youtube.com")
        return True, "Opening YouTube!"

    def send_whatsapp_message(self, phone_or_contact, message):
        """
        Send a WhatsApp message via WhatsApp Desktop app (Windows Store app).
        Uses whatsapp:// URI scheme which opens the native WhatsApp app.
        phone_or_contact: phone number with country code (e.g., "919876543210")
                          or contact name (will search in WhatsApp app)
        message: message text to send
        """
        import urllib.parse
        import subprocess

        # Clean phone number (remove non-digits)
        clean_phone = ''.join(filter(str.isdigit, phone_or_contact))

        if clean_phone and len(clean_phone) >= 10:
            # Phone number provided - use whatsapp:// URI scheme
            encoded_msg = urllib.parse.quote(message)
            url = f"whatsapp://send?phone={clean_phone}&text={encoded_msg}"
        else:
            # Contact name - just open WhatsApp app
            url = "whatsapp://"

        # Use start command to launch URI scheme
        try:
            subprocess.Popen(f'start "" "{url}"', shell=True)
            return True, f"Opening WhatsApp app to send message to {phone_or_contact}..."
        except Exception as e:
            # Fallback to WhatsApp Web
            if clean_phone and len(clean_phone) >= 10:
                encoded_msg = urllib.parse.quote(message)
                web_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"
            else:
                web_url = "https://web.whatsapp.com/"
            webbrowser.open(web_url)
            return True, f"Opening WhatsApp Web to send message to {phone_or_contact}..."

    # ── Screenshot ────────────────────────────────────────────────────────────

    def take_screenshot(self):
        try:
            shots_dir = os.path.join(self.user_dir, "Pictures", "Screenshots")
            os.makedirs(shots_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(shots_dir, f"buddy_shot_{ts}.png")
            img = ImageGrab.grab()
            img.save(filepath, "PNG")
            return True, f"Screenshot saved to {filepath}!"
        except Exception as e:
            # PowerShell fallback
            shots_dir = os.path.join(self.user_dir, "Pictures", "Screenshots")
            os.makedirs(shots_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(shots_dir, f"buddy_shot_{ts}.png")
            ps = f"""
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,
    [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen(0,0,0,0,$b.Size)
$b.Save('{filepath}', [System.Drawing.Imaging.ImageFormat]::Png)
"""
            try:
                subprocess.run(["powershell", "-Command", ps], check=True, capture_output=True)
                return True, f"Screenshot saved to {filepath}!"
            except Exception as ps_err:
                return False, f"Screenshot failed: {e} / {ps_err}"

    # ── System ────────────────────────────────────────────────────────────────

    def lock_workstation(self):
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "Computer locked. Guard your throne!"
        except Exception as e:
            return False, f"Could not lock screen: {e}"

    def get_system_stats(self):
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        bat_str = f", Battery: {battery.percent:.0f}%" if battery else ""
        return True, f"CPU: {cpu}% | RAM: {ram}%{bat_str}"

    def run_powershell(self, command, timeout=30):
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=timeout
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            if proc.returncode == 0:
                return True, out or "Done!"
            else:
                return False, f"Error ({proc.returncode}):\n{err or out}"
        except subprocess.TimeoutExpired:
            return False, f"Timed out after {timeout}s."
        except Exception as e:
            return False, f"Failed: {e}"

    def refresh_app_cache(self):
        """Force refresh the Start Menu app list cache."""
        global _start_apps_cache
        _start_apps_cache = None
        apps = _get_start_apps()
        return True, f"App cache refreshed — {len(apps)} apps found!"


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ex = SystemExecutor()
    print("Loading Start Menu apps...")
    apps = _get_start_apps()
    print(f"Found {len(apps)} apps")

    test_queries = ["whatsapp", "spotify", "apple music", "chrome", "calculator", "discord"]
    for q in test_queries:
        name, appid = _find_app_in_startmenu(q)
        print(f"  '{q}' → {name!r} ({appid})")
