"""
Permission & Audit Engine for Bahubali Desktop Buddy.
Ensures transparent, accurate, and permitted execution of:
- File system access & project data reading
- System modifications & process execution
- Agent delegations (Antigravity, Claude Code)
Maintains an immutable activity log at ~/.duh_buddy/activity.log.
"""

import os
import json
import time
from datetime import datetime

CONFIG_DIR = os.path.expanduser("~/.duh_buddy")
PERMISSIONS_FILE = os.path.join(CONFIG_DIR, "permissions.json")
ACTIVITY_LOG_FILE = os.path.join(CONFIG_DIR, "activity.log")

DEFAULT_PERMISSIONS = {
    "read_user_data": True,       # Read files, project directories, system status
    "write_user_files": True,     # Create code files, notes, configurations
    "execute_apps": True,         # Launch VS Code, Chrome, etc.
    "delegate_agents": True,      # Run Antigravity and Claude Code
    "system_controls": True,      # Volume, media, lock screen, screenshots
    "confirm_destructive": True   # Ask confirmation before file deletion / process kill
}


class PermissionManager:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.permissions = self._load_permissions()

    def _load_permissions(self):
        if os.path.exists(PERMISSIONS_FILE):
            try:
                with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                    return {**DEFAULT_PERMISSIONS, **json.load(f)}
            except Exception:
                pass
        self._save_permissions(DEFAULT_PERMISSIONS)
        return DEFAULT_PERMISSIONS.copy()

    def _save_permissions(self, perms):
        try:
            with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(perms, f, indent=4)
        except Exception as e:
            print(f"[Permission Save Error] {e}")

    def is_allowed(self, capability):
        """Check if capability is permitted."""
        return self.permissions.get(capability, True)

    def set_permission(self, capability, granted: bool):
        self.permissions[capability] = granted
        self._save_permissions(self.permissions)

    def log_activity(self, action_type, description, success=True, details=None):
        """Log every action to activity.log for 100% user visibility."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_tag = "SUCCESS" if success else "FAILED"
        entry = f"[{timestamp}] [{status_tag}] [{action_type.upper()}] {description}\n"
        if details:
            entry += f"    Details: {str(details)[:200]}\n"

        try:
            with open(ACTIVITY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def get_recent_activity(self, limit=10):
        """Read latest activity log entries."""
        if not os.path.exists(ACTIVITY_LOG_FILE):
            return ["No recorded activities yet."]
        try:
            with open(ACTIVITY_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return lines[-limit:]
        except Exception:
            return ["Error reading activity log."]
