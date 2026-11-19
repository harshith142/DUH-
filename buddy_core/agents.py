"""
Agent Delegator for Desktop Buddy.
Integrates directly with:
- Google Antigravity CLI (agy)
- Anthropic Claude Code (claude)
- Microsoft VS Code (code)
"""

import os
import subprocess
import threading
import shutil


class AgentManager:
    def __init__(self, workspace_dir=None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.agy_path = shutil.which("agy") or r"C:\Users\harshith1402\AppData\Local\agy\bin\agy.EXE"
        self.claude_path = shutil.which("claude") or r"C:\Users\harshith1402\AppData\Roaming\npm\claude.cmd"
        self.code_path = shutil.which("code") or r"C:\Users\harshith1402\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"

    def open_vscode(self, path=None, file=None, new_window=False):
        """Open VS Code at the specified path or file."""
        target = path or self.workspace_dir
        if file:
            target = os.path.join(target, file)

        cmd = [self.code_path]
        if new_window:
            cmd.append("-n")
        cmd.append(target)

        try:
            subprocess.Popen(cmd, shell=True)
            return True, f"Opened VS Code at {target}"
        except Exception as e:
            return False, f"Failed to open VS Code: {e}"

    def run_antigravity(self, prompt, effort="low", timeout=120):
        """
        Execute a prompt using Antigravity CLI non-interactively (agy -p).
        Returns (success: bool, output: str).
        """
        if not os.path.exists(self.agy_path) and not shutil.which("agy"):
            return False, "Antigravity CLI (agy) not found in PATH."

        cmd = [self.agy_path, "-p", prompt, "--effort", effort]
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.workspace_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            stdout, stderr = process.communicate(timeout=timeout)
            output = (stdout or "") + (stderr or "")

            if "GEMINI_API_KEY environment variable is not set" in output:
                return False, "Antigravity requires GEMINI_API_KEY to be set. You can set it in your environment or settings.json."

            if process.returncode == 0:
                return True, stdout.strip() or "Antigravity completed the task successfully!"
            else:
                return False, f"Antigravity exited with code {process.returncode}:\n{output[:500]}"
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Antigravity task timed out."
        except Exception as e:
            return False, f"Error running Antigravity: {e}"

    def run_claude(self, prompt, timeout=120):
        """
        Execute a prompt using Claude Code CLI non-interactively (claude -p).
        Returns (success: bool, output: str).
        """
        if not os.path.exists(self.claude_path) and not shutil.which("claude"):
            return False, "Claude Code CLI not found in PATH."

        # Pass < /dev/null via powershell / cmd to avoid stdin prompt warnings
        cmd = f'"{self.claude_path}" -p "{prompt}"'
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.workspace_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                shell=True
            )
            stdout, stderr = process.communicate(timeout=timeout)
            output = (stdout or "") + (stderr or "")

            if "Not logged in" in output or "run /login" in output:
                return False, "Claude Code is not logged in yet. Please run 'claude' in a terminal and complete login."

            if process.returncode == 0:
                return True, stdout.strip() or "Claude completed the task successfully!"
            else:
                return False, f"Claude Code response:\n{output[:500]}"
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Claude Code task timed out."
        except Exception as e:
            return False, f"Error running Claude Code: {e}"

    def launch_claude_in_vscode(self, workspace=None):
        """
        Open VS Code and launch an interactive terminal running Claude Code.
        """
        target = workspace or self.workspace_dir
        # Open VSCode first
        self.open_vscode(path=target)

        # Open a new PowerShell terminal running claude
        try:
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command", f"cd '{target}'; claude"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True, f"Launched Claude Code in new console for {target} and opened in VS Code!"
        except Exception as e:
            return False, f"Failed to launch Claude console: {e}"

    def launch_antigravity_terminal(self, workspace=None):
        """Open a dedicated terminal running Antigravity CLI."""
        target = workspace or self.workspace_dir
        try:
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command", f"cd '{target}'; agy"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True, f"Launched Antigravity interactive terminal for {target}"
        except Exception as e:
            return False, f"Failed to launch Antigravity: {e}"
