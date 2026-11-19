"""
LLM & AI Reasoning Engine for Bahubali Desktop Buddy ("Baahubali Edition").
Supports:
- Local Ollama API (llama3.2:latest) for instant, private, offline conversational reasoning & code advice.
- Google Antigravity CLI (agy) for autonomous agent software engineering.
- Anthropic Claude Code (claude) for deep coding & refactoring.
"""

import os
import json
import urllib.request
import urllib.error
import subprocess

OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:latest"

BAHUBALI_SYSTEM_PROMPT = (
    "You are Bahubali, the legendary Baahubali Desktop Companion & AI Commander. "
    "You are loyal, wise, heroic, and supremely accurate. "
    "You assist the user with coding, computer automation, task management, and technical wisdom. "
    "Keep responses concise (1 to 3 sentences suitable for speech and desktop bubbles), impactful, and precise. "
    "Infuse a proud, honorable Mahishmati warrior spirit where fitting, but prioritize 100% technical accuracy."
)


class LLMEngine:
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.system_prompt = BAHUBALI_SYSTEM_PROMPT

    def is_ollama_available(self):
        """Check if Ollama server is responding."""
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "Bahubali-Buddy"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def query(self, user_prompt, max_tokens=150, temperature=0.7):
        """
        Query local Ollama LLM.
        Returns (success: bool, response_text: str)
        """
        if not self.is_ollama_available():
            return False, "Ollama local LLM is currently sleeping. Run 'ollama serve' to activate my offline mind!"

        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": self.system_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                OLLAMA_API_URL,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Bahubali-Buddy"}
            )
            with urllib.request.urlopen(req, timeout=25.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                reply = result.get("response", "").strip()
                if reply:
                    return True, reply
                return False, "My warrior thoughts returned no words."
        except urllib.error.URLError as e:
            return False, f"LLM connection error: {e}"
        except Exception as e:
            return False, f"LLM reasoning error: {e}"

    def ask_code_advice(self, code_question):
        """Specialized prompt for coding assistance."""
        coding_prompt = (
            f"As an expert senior software architect, provide a precise, accurate, and concise answer to this developer question:\n"
            f"{code_question}\n"
            f"Keep explanation under 3 sentences and provide clean syntax."
        )
        return self.query(coding_prompt, max_tokens=200, temperature=0.3)
