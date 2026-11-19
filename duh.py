"""
Bahubali CLI ("Baahubali Edition") - Desktop Companion & Task Automation Interface.
Usage:
  duh start                    # Launch Bahubali on desktop
  duh "your command here"      # Send any task (Antigravity, Claude, Apps, Volume, etc.)
  duh say "message"            # Make Bahubali speak a message aloud
  duh state celebrate|sleep    # Trigger specific animation
  duh walk left|right|stop     # Command Bahubali to march or halt
  duh status                   # Check if Bahubali is currently active
  duh stop                     # Dismiss Bahubali
"""

import sys
import os
import subprocess
import argparse
import time

from buddy_core.ipc import IPCClient, DEFAULT_PORT
from buddy_core.config import load_config
from buddy_core.brain import BuddyBrain


def launch_daemon_background():
    """Launch DUH GUI process in the background using pythonw."""
    import platform
    user_profile = os.environ.get('USERPROFILE', '')
    candidates = [
        os.path.join(user_profile, r"AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"),
        os.path.join(user_profile, r"AppData\Local\Python\bin\pythonw.exe"),
        os.path.join(user_profile, r"AppData\Local\Programs\Python\Python314\pythonw.exe"),
        os.path.join(user_profile, r"AppData\Local\Programs\Python\Python313\pythonw.exe"),
        os.path.join(user_profile, r"AppData\Local\Programs\Python\Python312\pythonw.exe"),
        sys.executable.replace("python.exe", "pythonw.exe") if "python.exe" in sys.executable else sys.executable,
    ]
    pythonw = next((c for c in candidates if os.path.exists(c)), sys.executable)

    duh_root = os.path.dirname(os.path.abspath(__file__))
    gui_script = os.path.join(duh_root, "buddy_core", "gui.py")

    try:
        # Use PowerShell Start-Process so the GUI runs as a true independent desktop process
        ps_cmd = (
            f'Start-Process -FilePath "{pythonw}" '
            f'-ArgumentList "{gui_script}" '
            f'-WorkingDirectory "{duh_root}" '
            f'-WindowStyle Hidden'
        )
        subprocess.Popen(
            ['powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command', ps_cmd],
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        client = IPCClient()
        for _ in range(30):
            time.sleep(0.3)
            if client.is_daemon_running():
                return True
        return False
    except Exception as e:
        print(f"[Error launching DUH] {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Bahubali: Baahubali Desktop Companion & AI Agent Delegator",
        add_help=True
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand")

    # duh start
    p_start = subparsers.add_parser("start", help="Launch Bahubali on your desktop")

    # duh say <msg>
    p_say = subparsers.add_parser("say", help="Make Bahubali speak aloud")
    p_say.add_argument("message", type=str, help="Message to speak")

    # duh state <anim>
    p_state = subparsers.add_parser("state", help="Set animation state (idle, walk, celebrate, think, sleep)")
    p_state.add_argument("animation", type=str, help="Animation state")

    # duh walk <direction>
    p_walk = subparsers.add_parser("walk", help="Command walk (left, right, stop, toggle)")
    p_walk.add_argument("direction", type=str, nargs="?", default="toggle", help="left, right, stop, or toggle")

    # duh status
    p_status = subparsers.add_parser("status", help="Check if Bahubali is active")

    # duh stop
    p_stop = subparsers.add_parser("stop", help="Close Bahubali")

    # Parse args or handle plain query: `duh "ask antigravity to ..."`
    if len(sys.argv) > 1 and sys.argv[1] not in ["start", "say", "state", "walk", "status", "stop", "-h", "--help"]:
        # Direct query
        query = " ".join(sys.argv[1:])
        client = IPCClient()
        if not client.is_daemon_running():
            print("[Bahubali is not running on desktop. Starting Bahubali...]")
            if launch_daemon_background():
                print("[Bahubali summoned to desktop successfully!]")
            else:
                # Fallback to direct brain execution
                print("[Executing directly via headless brain...]")
                brain = BuddyBrain()
                reply, _, _ = brain.process(query)
                print(f"Bahubali: {reply}")
                return

        resp = client.send_command("query", query)
        print(f"⚔️ Bahubali: {resp.get('reply', 'Order dispatched.')}")
        return

    args = parser.parse_args()
    client = IPCClient()

    if args.subcommand == "start" or len(sys.argv) == 1:
        if client.is_daemon_running():
            print("⚔️ Bahubali is already standing guard on your desktop!")
            client.send_command("say", "Jai Mahishmati! I am already here at your service!")
        else:
            print("🚀 Summoning Bahubali to your desktop...")
            if launch_daemon_background():
                print("⚔️ Jai Mahishmati! Bahubali is now active on your desktop above the taskbar.")
            else:
                print("Launching in foreground...")
                from buddy_core.gui import launch_gui
                launch_gui()

    elif args.subcommand == "say":
        if not client.is_daemon_running():
            print("Bahubali is not active. Starting...")
            launch_daemon_background()
        resp = client.send_command("say", args.message)
        print(f"⚔️ {resp.get('reply', 'Spoken.')}")

    elif args.subcommand == "state":
        if client.is_daemon_running():
            resp = client.send_command("state", args.animation)
            print(f"⚔️ {resp.get('reply', 'State changed.')}")
        else:
            print("Bahubali is not running. Run 'duh start' first.")

    elif args.subcommand == "walk":
        if client.is_daemon_running():
            resp = client.send_command("walk", args.direction)
            print(f"⚔️ {resp.get('reply', 'Walk updated.')}")
        else:
            print("Bahubali is not running. Run 'duh start' first.")

    elif args.subcommand == "status":
        if client.is_daemon_running():
            print("⚔️ Bahubali Status: ONLINE (Active on desktop, ready for commands)")
        else:
            print("⚔️ Bahubali Status: OFFLINE (Run 'duh start' to summon)")

    elif args.subcommand == "stop":
        if client.is_daemon_running():
            resp = client.send_command("exit", "")
            print(f"⚔️ {resp.get('reply', 'Bahubali dismissed.')}")
        else:
            print("Bahubali is not running.")


if __name__ == "__main__":
    main()
