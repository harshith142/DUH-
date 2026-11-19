"""
Brain / NLP Intent Classifier and Guidance Engine for Desktop Buddy Bahubali ("Baahubali Edition").
Routes natural language inputs from Voice, CLI, and GUI to:
- Task Reminder & Scheduling Engine (reminders.py)
- Developer & Coding Assistant (coding_assistant.py, Antigravity, Claude Code in VS Code)
- Offline & Local LLM Intelligence (Ollama llama3.2 via llm.py)
- System automation (apps, volume, screen, files via executor.py)
- Physical warrior animations (walk, meditate, celebrate, think, talk)
"""

import re
import os
import random
from .executor import SystemExecutor
from .agents import AgentManager
from .reminders import ReminderManager
from .coding_assistant import CodingAssistant
from .llm import LLMEngine
from .permissions import PermissionManager


BAHUBALI_GREETINGS = [
    "Jai Mahishmati! I am Bahubali — your desktop guardian! Commander of Antigravity, master of Claude Code in VS Code, and protector of this realm!",
    "By the decree of Sivagami Devi, Bahubali stands guard over your workstation! What task shall we conquer today?",
    "Greetings, Commander! Whether it is coding in VS Code, delegating to Antigravity, setting reminders, or commanding Windows, Mahishmati obeys!"
]

BAHUBALI_VICTORY_ROARS = [
    "Jai Mahishmati! Victory is ours!",
    "A warrior's courage never bends! The objective has been conquered!",
    "By strength and intellect, Mahishmati triumphs once again!"
]


class BuddyBrain:
    def __init__(self, buddy_ui_ref=None):
        self.name = "Bahubali"
        self.ui = buddy_ui_ref
        self.executor = SystemExecutor()
        self.agents = AgentManager()
        self.reminders = ReminderManager(on_trigger_callback=self._handle_reminder_trigger)
        self.coder = CodingAssistant()
        self.llm = LLMEngine()
        self.perms = PermissionManager()

    def _handle_reminder_trigger(self, rem):
        """Called when a scheduled reminder is due."""
        text = rem.get("text", "Task reminder")
        announcement = f"Commander! Your reminder has arrived: {text}! Jai Mahishmati!"
        if self.ui:
            self.ui.root.after(0, lambda: self.ui.say(announcement, state="celebrate", duration=12))

    def process(self, query):
        """
        Process user query string and return:
        (reply_text: str, animation_state: str, action_details: dict)
        """
        if not query or not query.strip():
            return "Speak, Commander! What task shall Mahishmati conquer?", "idle", {}

        q = query.lower().strip()

        # Clean "hey bahubali", "bahubali", "hey baahubali", "baahubali", "hey buddy" prefix if present
        clean_q = re.sub(r'^(hey\s+)?(bahubali|baahubali|buddy)\s*,?\s*', '', q).strip()

        # 0. Baahubali Lore & Iconic Triggers
        if any(k in clean_q for k in ["jai mahishmati", "mahishmati", "amarendra", "mahendra"]):
            self.perms.log_activity("lore", "Jai Mahishmati invoked")
            return (
                "JAI MAHISHMATI! My sword, my strength, and my code are pledged to the realm!",
                "celebrate",
                {"lore": True}
            )

        if "kattappa" in clean_q:
            return (
                "Kattappa followed dharma and royal oath, but in our realm of code, only bug-free commits survive!",
                "think",
                {}
            )

        if "bhallaladeva" in clean_q:
            return (
                "Bhallaladeva's treachery cannot match our unity! Antigravity and Claude shall vanquish all obstacles!",
                "celebrate",
                {}
            )

        if any(k in clean_q for k in ["shiva lingam", "lift lingam", "lift the shiva lingam"]):
            return (
                "With devotion and titanic strength, the Shiva Lingam is lifted on Mahishmati's shoulders! Har Har Mahadev!",
                "celebrate",
                {}
            )

        # 1. Reminders & Scheduling
        if any(k in clean_q for k in ["remind me", "set reminder", "set a reminder", "schedule a reminder"]):
            success, msg, rem_obj = self.reminders.parse_and_schedule(clean_q)
            self.perms.log_activity("reminder_create", msg, success=success)
            return msg, "celebrate" if success else "think", {"reminder": rem_obj}

        if any(k in clean_q for k in ["list reminders", "show reminders", "what are my reminders", "pending reminders"]):
            pending = self.reminders.list_pending()
            if not pending:
                return "The royal calendar is clear! You have no pending reminders.", "talk", {}
            lines = [f"• {r['text']} (at {r['trigger_str']})" for r in pending[:5]]
            summary = "Your pending reminders:\n" + "\n".join(lines)
            return summary, "talk", {"reminders": pending}

        if any(k in clean_q for k in ["clear reminders", "delete all reminders", "cancel reminders"]):
            self.reminders.clear_all()
            self.perms.log_activity("reminder_clear", "All reminders cleared")
            return "All scheduled reminders have been dismissed by royal decree.", "celebrate", {}

        # 2. Antigravity Delegation
        if any(k in q for k in ["antigravity", "agy", "ask antigravity", "tell antigravity"]):
            prompt = re.sub(r'^(hey\s+)?(bahubali|baahubali|buddy)?\s*(ask|tell|run)?\s*(antigravity|agy)\s*(to|that)?\s*', '', query, flags=re.IGNORECASE).strip()
            if not prompt:
                return "What mighty mission shall I command Antigravity to achieve?", "think", {"type": "agy_prompt"}

            self.perms.log_activity("antigravity_delegation", prompt)
            success, result = self.coder.delegate_to_antigravity(prompt)
            if success:
                summary = result[:160] + ("..." if len(result) > 160 else "")
                return f"Antigravity conquered the quest: {summary}", "celebrate", {"output": result}
            else:
                return f"Antigravity report: {result[:130]}", "think", {"error": result}

        # 3. Claude Code in VS Code Delegation
        if any(k in q for k in ["claude", "ask claude", "tell claude"]):
            prompt = re.sub(r'^(hey\s+)?(bahubali|baahubali|buddy)?\s*(ask|tell|run)?\s*claude\s*(to|in vscode to|that)?\s*', '', query, flags=re.IGNORECASE).strip()
            if any(k in q for k in ["interactive", "terminal", "open claude"]):
                success, msg = self.agents.launch_claude_in_vscode()
                self.perms.log_activity("claude_launch", msg, success=success)
                return f"Jai Mahishmati! {msg}", "celebrate", {}

            if not prompt:
                return "What engineering challenge shall I summon Claude Code to solve?", "think", {}

            self.perms.log_activity("claude_delegation", prompt)
            success, result = self.coder.delegate_to_claude(prompt)
            if success:
                summary = result[:160] + ("..." if len(result) > 160 else "")
                return f"Claude in VS Code has finished: {summary}", "celebrate", {"output": result}
            else:
                return f"Claude report: {result[:130]}", "think", {"error": result}

        # 4. VS Code & Git Operations
        if any(k in q for k in ["open vscode", "open code", "launch vscode", "open in vscode", "start vscode"]):
            path = None
            if "here" in q or "this directory" in q:
                path = os.getcwd()
            success, msg = self.agents.open_vscode(path=path)
            self.perms.log_activity("open_vscode", msg, success=success)
            return ("Opening VS Code fortress as commanded!", "celebrate", {}) if success else (msg, "think", {})

        if any(k in clean_q for k in ["git status", "repo status", "branch status"]):
            success, msg = self.coder.get_git_status()
            return msg, "talk" if success else "think", {}

        if any(k in clean_q for k in ["git diff", "git changes", "what did i change"]):
            success, msg = self.coder.get_git_diff_summary()
            return f"Git changes summary:\n{msg[:250]}", "talk", {}

        if any(k in clean_q for k in ["scan workspace", "list files", "what files are here", "workspace files"]):
            success, msg = self.coder.scan_workspace_files()
            return msg, "talk", {}

        # 5. Physical Movements & Warrior Stances
        if any(k in clean_q for k in ["walk left", "go left", "march left", "move left"]):
            if self.ui:
                self.ui.set_motion("left")
            return "Marching to the left flanks of Mahishmati!", "walk_left", {}

        if any(k in clean_q for k in ["walk right", "go right", "march right", "move right"]):
            if self.ui:
                self.ui.set_motion("right")
            return "Advancing forward to the right!", "walk_right", {}

        if any(k in clean_q for k in ["stop walking", "halt walking", "stay here", "freeze", "stand still"]) or (clean_q in ["halt", "pause", "stop"] and "music" not in clean_q and "song" not in clean_q):
            if self.ui:
                self.ui.set_motion("stop")
            return "Standing guard at your side, Commander.", "idle", {}

        if any(k in clean_q for k in ["dance", "jump", "celebrate", "victory", "roar", "sword"]):
            return random.choice(BAHUBALI_VICTORY_ROARS), "celebrate", {}

        if any(k in clean_q for k in ["sleep", "go to sleep", "meditate", "rest", "take a nap"]):
            return "Entering deep warrior meditation... Chant 'Hey Bahubali' whenever you need my sword!", "sleep", {}

        # 6. Volume & Media Controls
        if "mute" in clean_q or "unmute" in clean_q:
            success, msg = self.executor.change_volume("mute")
            return f"By royal decree, {msg.lower()}", "talk", {}

        if any(k in clean_q for k in ["volume up", "louder", "turn up sound"]):
            success, msg = self.executor.change_volume("up", 10)
            return "Raising the battle horns! Volume up.", "talk", {}

        if any(k in clean_q for k in ["volume down", "quieter", "lower volume", "turn down sound"]):
            success, msg = self.executor.change_volume("down", 10)
            return "Silencing the court. Volume lowered.", "talk", {}

        # ── 6b. Advanced Music & Song Playback (Apple Music / Spotify / Local) ──
        if any(k in clean_q for k in ["pause music", "stop music", "halt music", "pause song"]):
            self.executor.media_control("play_pause")
            return "Music paused at your command, Commander.", "talk", {}

        if any(k in clean_q for k in ["next song", "next track", "skip song", "skip track"]):
            self.executor.media_control("next")
            return "Next royal battle anthem!", "celebrate", {}

        if any(k in clean_q for k in ["previous song", "prev song", "last song", "back song"]):
            self.executor.media_control("prev")
            return "Returning to the previous symphony!", "talk", {}

        if clean_q in ["resume music", "play music", "unpause music", "continue music", "play songs", "play"]:
            success, msg = self.executor.play_music("")
            return msg, "celebrate", {}

        # Spotify: "play believer on spotify", "spotify play taylor swift", "open spotify"
        spotify_match = re.search(r'(?:play\s+(.+?)\s+(?:on|in)\s+spotify|spotify\s+(?:play\s+)?(.+))', clean_q, re.IGNORECASE)
        if "spotify" in clean_q and (spotify_match or clean_q in ["open spotify", "launch spotify", "spotify"]):
            song = ""
            if spotify_match:
                song = (spotify_match.group(1) or spotify_match.group(2) or "").strip()
            success, msg = self.executor.play_spotify(song)
            self.perms.log_activity("play_music", f"Spotify: {song or 'playback'}", success=success)
            return msg, "celebrate", {}

        # Local music: "play local music", "play my music", "play believer locally"
        local_match = re.search(r'(?:play\s+(.+?)\s+(?:locally|local music|on my pc)|play local music|play my music)', clean_q, re.IGNORECASE)
        if any(k in clean_q for k in ["local music", "my music", "music on pc", "music on my computer"]) or local_match:
            song = local_match.group(1).strip() if local_match and local_match.group(1) else ""
            success, msg = self.executor.play_local_music(song)
            self.perms.log_activity("play_music", f"Local: {song or 'playback'}", success=success)
            return msg, "celebrate" if success else "think", {}

        # Check for specific YouTube music request (e.g. "play dude on youtube")
        yt_music_match = re.search(r'play\s+(.+?)\s+(?:on|in)\s+youtube', clean_q, re.IGNORECASE)
        if yt_music_match:
            song = yt_music_match.group(1).strip()
            self.executor.search_youtube(song)
            self.perms.log_activity("youtube_music", song)
            return f"Playing '{song}' on YouTube, Commander!", "celebrate", {}

        # General Music & Song Request (Defaults to Apple Music as requested!)
        # Matches: "play dude songs in apple music", "apple music and play dude songs",
        #          "play dude songs", "play believer", "play taylor swift", etc.
        if "apple music" in clean_q or clean_q.startswith("play ") or clean_q.startswith("listen to "):
            song = clean_q
            # Strip trailing "in apple music", "on apple music"
            song = re.sub(r'\s+(?:in|on)\s+apple\s*music$', '', song, flags=re.IGNORECASE).strip()
            # Strip leading "open apple music and play", "apple music and play"
            song = re.sub(r'^(?:open\s+)?apple\s*music\s+(?:and\s+)?play\s+', '', song, flags=re.IGNORECASE).strip()
            # Strip leading "play song", "play songs", "play", "listen to"
            song = re.sub(r'^(?:play\s+songs?\s+|play\s+|listen\s+to\s+)', '', song, flags=re.IGNORECASE).strip()
            # Strip trailing "songs", "song", "music", "tracks"
            song = re.sub(r'\s+(?:songs?|music|tracks?)$', '', song, flags=re.IGNORECASE).strip()

            if song in ['', 'songs', 'song', 'music']:
                song = ""

            success, msg = self.executor.play_music(song, service="apple_music")
            self.perms.log_activity("play_music", f"Apple Music: {song or 'playback'}", success=success)
            return msg, "celebrate", {}

        # ── 6c. System Controls & Utilities (Brightness, Notifications, etc.) ──
        # Brightness: "set brightness to 50", "brightness up/down", "what is brightness"
        if any(k in clean_q for k in ["brightness", "screen brightness"]):
            m = re.search(r'brightness\s+(?:to\s+)?(\d{1,3})', clean_q)
            if m:
                level = int(m.group(1))
                success, msg = self.executor.set_brightness(level)
                self.perms.log_activity("set_brightness", f"{level}%", success=success)
                return msg, "talk", {}
            if "up" in clean_q or "increase" in clean_q:
                success, msg = self.executor.get_brightness()
                return msg, "talk", {}
            if "down" in clean_q or "decrease" in clean_q:
                return "Brightness down control coming next update, Commander!", "talk", {}
            success, msg = self.executor.get_brightness()
            return msg, "talk", {}

        # Toast / Notification: "show notification hello", "send toast test"
        if any(k in clean_q for k in ["show notification", "send toast", "notify me", "desktop notification"]):
            title = "Bahubali"
            msg_text = clean_q
            for prefix in ["show notification", "send toast", "notify me", "desktop notification"]:
                msg_text = re.sub(re.escape(prefix), "", msg_text, flags=re.IGNORECASE).strip()
            if not msg_text:
                msg_text = "Bahubali is standing guard!"
            success, result = self.executor.show_toast(title, msg_text)
            self.perms.log_activity("toast", msg_text, success=success)
            return result, "talk", {}

        # Recycle bin: "empty recycle bin", "clear recycle bin"
        if any(k in clean_q for k in ["empty recycle bin", "clear recycle bin", "empty trash"]):
            success, msg = self.executor.empty_recycle_bin()
            self.perms.log_activity("empty_recycle_bin", msg, success=success)
            return msg, "celebrate" if success else "think", {}

        # Kill process: "kill chrome", "close notepad", "terminate spotify"
        kill_match = re.search(r'(?:kill|close|terminate)\s+(.+)', clean_q)
        if kill_match and any(k in clean_q for k in ["kill ", "close ", "terminate "]):
            proc = kill_match.group(1).strip()
            success, msg = self.executor.kill_process(proc)
            self.perms.log_activity("kill_process", proc, success=success)
            return msg, "talk", {}

        # List processes: "list processes", "running processes", "what is running"
        if any(k in clean_q for k in ["list processes", "running processes", "what is running", "process list"]):
            success, msg = self.executor.list_running_processes()
            self.perms.log_activity("list_processes", msg, success=success)
            return msg, "talk", {}

        # Open folder: "open folder downloads", "open directory documents"
        # Only matches when "folder" or "directory" keyword is explicitly used
        folder_match = re.search(r'open\s+(?:folder|directory)\s+(.+)', clean_q)
        if any(k in clean_q for k in ["open folder", "open directory"]) and folder_match:
            folder = folder_match.group(1).strip()
            # Map common folder names
            folder_map = {
                "downloads": os.path.join(self.executor.user_dir, "Downloads"),
                "documents": os.path.join(self.executor.user_dir, "Documents"),
                "desktop": os.path.join(self.executor.user_dir, "Desktop"),
                "pictures": os.path.join(self.executor.user_dir, "Pictures"),
                "music": os.path.join(self.executor.user_dir, "Music"),
                "videos": os.path.join(self.executor.user_dir, "Videos"),
            }
            target = folder_map.get(folder.lower(), folder)
            success, msg = self.executor.open_folder(target)
            self.perms.log_activity("open_folder", target, success=success)
            return msg, "celebrate" if success else "think", {}

        # Create note: "create note", "make note", "sticky note", "write note"
        note_match = re.search(r'(?:create|make|write)\s+(?:a\s+)?(?:note|sticky note)\s+(?:called\s+|titled\s+|named\s+)?(.+)', clean_q)
        if any(k in clean_q for k in ["create note", "make note", "write note", "sticky note"]):
            title = note_match.group(1).strip() if note_match and note_match.group(1) else ""
            content = ""
            if " with content " in clean_q:
                content = clean_q.split("with content", 1)[1].strip()
            elif " saying " in clean_q:
                content = clean_q.split("saying", 1)[1].strip()
            success, msg = self.executor.create_note(title, content)
            self.perms.log_activity("create_note", title or "untitled", success=success)
            return msg, "celebrate" if success else "think", {}

        # Weather: "weather", "weather in london", "what is the weather"
        weather_match = re.search(r'weather(?:\s+in\s+|\s+for\s+|\s+at\s+)?(.+)', clean_q)
        if clean_q in ["weather", "what is the weather", "tell me the weather"] or weather_match:
            city = weather_match.group(1).strip() if weather_match else ""
            success, msg = self.executor.get_weather(city)
            self.perms.log_activity("weather", city or "current location", success=success)
            return msg, "talk", {}

        # 7. Screenshot & Screen Lock
        if any(k in clean_q for k in ["screenshot", "take a screenshot", "capture screen"]):
            success, msg = self.executor.take_screenshot()
            self.perms.log_activity("screenshot", msg, success=success)
            return f"Captured! {msg}", "celebrate", {}

        if any(k in clean_q for k in ["lock screen", "lock computer", "lock pc"]):
            self.executor.lock_workstation()
            self.perms.log_activity("lock_workstation", "Workstation locked")
            return "Securing the fortress gates! Workstation locked.", "idle", {}

        # 8. System Metrics & Activity Log
        if any(k in clean_q for k in ["battery", "cpu", "ram", "system stats", "pc status"]):
            success, msg = self.executor.get_system_stats()
            return f"Fortress diagnostics: {msg}", "talk", {}

        if any(k in clean_q for k in ["activity log", "what did you do", "recent actions"]):
            logs = self.perms.get_recent_activity(5)
            clean_logs = [l.strip() for l in logs if l.strip()]
            return "Recent activity log:\n" + "\n".join(clean_logs[-4:]), "talk", {}

        # 9. Web Browsing & Search
        if "search youtube for" in clean_q or "youtube search" in clean_q:
            term = re.sub(r'.*search youtube for\s*', '', clean_q, flags=re.IGNORECASE).strip()
            self.executor.search_youtube(term)
            self.perms.log_activity("youtube_search", term)
            return f"Summoning YouTube scrolls for '{term}'!", "celebrate", {}

        if "search google for" in clean_q or "search for" in clean_q or clean_q.startswith("google "):
            term = re.sub(r'.*search (google for|for)?\s*', '', clean_q, flags=re.IGNORECASE).strip()
            # Also handle "google <term>" case
            if clean_q.startswith("google "):
                term = clean_q[7:].strip()
            self.executor.open_url_or_search(term, is_search=True)
            self.perms.log_activity("web_search", term)
            return f"Scouting the world web for '{term}'!", "celebrate", {}

        # 9b. WhatsApp Messaging
        if any(k in clean_q for k in ["send whatsapp", "whatsapp message", "message on whatsapp"]):
            # Parse: "send whatsapp to 9876543210 saying hello" or "whatsapp message to john saying hi"
            phone_match = re.search(r'(?:send\s+whatsapp|whatsapp\s+message|message\s+on\s+whatsapp)\s+(?:to\s+)?([^,\s]+(?:\s+[^,\s]+)*)\s+(?:saying|msg|message)\s+(.*)', query, re.IGNORECASE)
            if phone_match:
                phone_or_contact = phone_match.group(1).strip()
                message = phone_match.group(2).strip()
            else:
                # Simpler: "whatsapp 9876543210 hello" or "whatsapp john hello"
                parts = query.split(None, 2)
                if len(parts) >= 3:
                    phone_or_contact = parts[1]
                    message = parts[2]
                else:
                    return "Commander, please specify: 'send whatsapp to <number/contact> saying <message>'", "think", {}

            success, msg = self.executor.send_whatsapp_message(phone_or_contact, message)
            self.perms.log_activity("whatsapp_send", f"{phone_or_contact}: {message[:30]}", success=success)
            return f"Jai Mahishmati! {msg}", "celebrate", {}

        # 10. List all installed apps (to discover app names)
        if any(k in clean_q for k in ["list apps", "show apps", "installed apps", "what apps", "all apps"]):
            success, msg = self.executor.list_all_apps()
            self.perms.log_activity("list_apps", msg, success=success)
            return msg, "talk", {}

        # 10b. Open all apps (launch every installed app)
        if any(k in clean_q for k in ["open all apps", "launch all apps", "open every app"]):
            success, msg = self.executor.open_all_apps()
            self.perms.log_activity("open_all_apps", msg, success=success)
            return msg, "celebrate" if success else "think", {}

        # 10c. Application Launching - open any specific app
        if clean_q.startswith("open ") or clean_q.startswith("launch "):
            app = re.sub(r'^(open|launch)\s+', '', clean_q).strip()
            success, msg = self.executor.open_app(app)
            self.perms.log_activity("open_app", f"{app}: {msg}", success=success)
            return msg, "celebrate" if success else "think", {}

        # 11. Greetings & Identity
        if any(k in clean_q for k in ["hello", "hi", "hey", "who are you", "what can you do", "help", "guide me"]):
            return random.choice(BAHUBALI_GREETINGS), "celebrate", {}

        # 12. Intelligent Local LLM Fallback (Ollama llama3.2)
        # Any question, code advice, general chat or query is processed by the LLM
        if self.llm.is_ollama_available():
            self.perms.log_activity("llm_query", query[:50])
            success, llm_reply = self.llm.query(query)
            if success and llm_reply:
                return llm_reply, "talk", {"source": "ollama"}

        # 13. Fallback when LLM is unavailable
        return (
            f"Commander, shall I delegate '{query}' to Antigravity or Claude Code in VS Code?",
            "think",
            {"unhandled_query": query}
        )
