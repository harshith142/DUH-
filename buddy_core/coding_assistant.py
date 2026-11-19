"""
Developer & Coding Assistant Module for Bahubali Desktop Buddy.
Integrates:
- Git repository operations (status, diff summary, commit assistant)
- Workspace and file analysis with user permission
- Antigravity autonomous coding agent delegation
- Claude Code in VS Code delegation
- High-accuracy code advice & debugging powered by LLM
"""

import os
import subprocess
import shutil
from .agents import AgentManager
from .llm import LLMEngine
from .permissions import PermissionManager


class CodingAssistant:
    def __init__(self, workspace_path=None):
        self.workspace_path = workspace_path or os.getcwd()
        self.agents = AgentManager(workspace_dir=self.workspace_path)
        self.llm = LLMEngine()
        self.perms = PermissionManager()

    def get_git_status(self):
        """Get git repository branch and status in current workspace."""
        if not self.perms.is_allowed("read_user_data"):
            return False, "Permission denied to read repository data."

        try:
            res = subprocess.run(
                ["git", "status", "--short", "--branch"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                lines = res.stdout.strip().split("\n")
                branch_line = lines[0] if lines else "unknown"
                modified = [l for l in lines[1:] if l.strip()]
                summary = f"Git {branch_line}. Modified files: {len(modified)}"
                if modified:
                    file_list = ", ".join([l.strip().split()[-1] for l in modified[:4]])
                    summary += f" ({file_list}{'...' if len(modified) > 4 else ''})"
                self.perms.log_activity("git_status", summary, success=True)
                return True, summary
            return False, "Not inside a git repository or git error."
        except Exception as e:
            return False, f"Git check error: {e}"

    def get_git_diff_summary(self):
        """Get summary of recent unstaged/staged git diff."""
        try:
            res = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=6
            )
            output = res.stdout.strip()
            if output:
                return True, output
            return True, "Working tree is clean, no modified files."
        except Exception as e:
            return False, f"Git diff error: {e}"

    def scan_workspace_files(self, limit=15):
        """List relevant code files in workspace."""
        if not self.perms.is_allowed("read_user_data"):
            return False, "Permission denied to scan workspace."

        try:
            files_found = []
            for root, dirs, files in os.walk(self.workspace_path):
                # Ignore hidden and virtual env folders
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                for f in files:
                    if f.endswith(('.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.java', '.cpp', '.sql')):
                        rel = os.path.relpath(os.path.join(root, f), self.workspace_path)
                        files_found.append(rel)
                        if len(files_found) >= limit:
                            break
                if len(files_found) >= limit:
                    break

            if files_found:
                msg = f"Workspace files: {', '.join(files_found[:8])}"
                if len(files_found) > 8:
                    msg += f" ... (+{len(files_found)-8} more)"
                return True, msg
            return True, "No code files found in current directory."
        except Exception as e:
            return False, f"Scan error: {e}"

    def explain_code_or_error(self, code_query):
        """Use LLM to explain code, syntax, or error stack traces."""
        success, answer = self.llm.ask_code_advice(code_query)
        self.perms.log_activity("llm_code_advice", f"Query: {code_query[:50]}", success=success)
        return success, answer

    def delegate_to_antigravity(self, prompt):
        """Run Antigravity autonomous software agent on prompt."""
        self.perms.log_activity("antigravity_task", prompt)
        return self.agents.run_antigravity(prompt)

    def delegate_to_claude(self, prompt):
        """Run Claude Code on prompt."""
        self.perms.log_activity("claude_task", prompt)
        return self.agents.run_claude(prompt)
