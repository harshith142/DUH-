"""
Desktop Buddy GUI ("Baahubali Edition") for Bahubali.
A transparent, animated desktop companion that walks above your taskbar,
speaks via native SAPI5 TTS, listens via microphone, and executes Antigravity,
Claude Code in VS Code, Reminders, and Windows system automation.
"""

import os
import sys
import time
import math
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from buddy_core.config import load_config, save_config
    from buddy_core.sprites import SpriteManager
    from buddy_core.brain import BuddyBrain
    from buddy_core.tts import TTSEngine
    from buddy_core.stt import STTEngine
    from buddy_core.ipc import IPCServer, DEFAULT_PORT
    try:
        from buddy_core.tray import TrayManager
    except Exception:
        TrayManager = None
else:
    from .config import load_config, save_config
    from .sprites import SpriteManager
    from .brain import BuddyBrain
    from .tts import TTSEngine
    from .stt import STTEngine
    from .ipc import IPCServer, DEFAULT_PORT
    try:
        from .tray import TrayManager
    except Exception:
        TrayManager = None


TRANSPARENT_COLOR = "#010101"


class DesktopBuddyGUI:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title(f"{self.config.get('name', 'Bahubali')} - Baahubali Desktop Buddy")

        # Configure transparent frameless always-on-top window
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.root.config(bg=TRANSPARENT_COLOR)

        # Screen dimensions
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # Buddy dimensions & positioning
        self.char_w = 100
        self.char_h = 100
        self.bubble_w = 360
        self.bubble_h = 190
        self.win_w = max(self.char_w, self.bubble_w) + 40
        self.win_h = self.char_h + self.bubble_h + 30

        # Position at bottom right above taskbar
        self.x = self.screen_w - self.win_w - 60
        self.y = self.screen_h - self.win_h - self.config.get("screen_margin", 40)
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.x}+{self.y}")

        # Core Engines
        self.sprite_mgr = SpriteManager()
        self.brain = BuddyBrain(buddy_ui_ref=self)
        self.tray = TrayManager(gui_ref=self) if TrayManager else None
        self.voice_muted = False
        self.tts = TTSEngine(
            voice_idx=self.config.get("voice_index", 0),
            rate=self.config.get("voice_rate", 1),
            volume=self.config.get("voice_volume", 100)
        )
        self.stt = STTEngine(
            energy_threshold=self.config.get("energy_threshold", 500),
            whisper_model=self.config.get("whisper_model", "base"),
            wake_words=self.config.get("wake_words", ["hey bahubali", "bahubali", "hey baahubali", "baahubali", "hey buddy"])
        )

        # Setup TTS Callbacks for synchronized talking animation
        self.tts.set_callbacks(
            on_start=self._on_speech_start,
            on_end=self._on_speech_end
        )

        # Motion & Animation state
        self.auto_walk = self.config.get("auto_walk", True)
        self.walk_direction = "left"  # "left" or "right"
        self.walk_speed = self.config.get("walk_speed", 3)
        self.walk_step_counter = 0
        self.walk_pause_until = 0
        self.current_state = "idle"
        self.previous_state = "idle"
        self.bubble_hide_time = 0
        self.is_listening = False
        self.auto_listen_enabled = False

        # Dragging support
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Build Canvas & UI Elements
        self._setup_ui()

        # IPC Server for CLI compliance
        self.ipc_server = IPCServer(
            port=self.config.get("ipc_port", DEFAULT_PORT),
            message_handler=self._handle_ipc_message
        )
        self.ipc_server.start()

        # Animation Loop
        self._tick_interval_ms = int(1000 / self.config.get("fps", 24))
        self.root.after(self._tick_interval_ms, self._animation_loop)

        # Greet user on launch
        self.root.after(500, self._initial_greeting)

    def _setup_ui(self):
        """Create transparent canvas and overlay widgets."""
        self.canvas = tk.Canvas(
            self.root,
            width=self.win_w,
            height=self.win_h,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Character Sprite Item on Canvas (bottom centered)
        self.char_canvas_x = self.win_w // 2
        self.char_canvas_y = self.win_h - (self.char_h // 2) - 5
        self._current_tk_img = None
        self.char_sprite_id = self.canvas.create_image(
            self.char_canvas_x,
            self.char_canvas_y,
            image=None
        )

        # Speech Bubble Container (Toplevel frame inside canvas)
        self.bubble_frame = tk.Frame(
            self.root,
            bg="#0f172a",          # Slate-900
            bd=2,
            relief="solid",
            highlightbackground="#f59e0b",  # Amber-500 Royal Gold
            highlightcolor="#f59e0b",
            highlightthickness=2
        )

        # Title & Badge Bar
        header_bar = tk.Frame(self.bubble_frame, bg="#1e293b")
        header_bar.pack(fill="x", padx=2, pady=2)

        self.title_label = tk.Label(
            header_bar,
            text=f"⚔️ {self.config.get('name', 'Bahubali')}  •  Mahishmati Commander",
            font=("Segoe UI", 9, "bold"),
            fg="#fbbf24",          # Golden Yellow
            bg="#1e293b"
        )
        self.title_label.pack(side="left", padx=6, pady=2)

        # Mute toggle button
        self.mute_btn = tk.Label(
            header_bar,
            text="🔊",
            font=("Segoe UI", 9),
            fg="#e2e8f0",
            bg="#1e293b",
            cursor="hand2"
        )
        self.mute_btn.pack(side="right", padx=4)
        self.mute_btn.bind("<Button-1>", lambda e: self.toggle_mute())

        # Close bubble button
        close_btn = tk.Label(
            header_bar,
            text="×",
            font=("Segoe UI", 11, "bold"),
            fg="#94a3b8",
            bg="#1e293b",
            cursor="hand2"
        )
        close_btn.pack(side="right", padx=4)
        close_btn.bind("<Button-1>", lambda e: self.hide_bubble())

        # Speech message label
        self.message_label = tk.Label(
            self.bubble_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#f8fafc",
            bg="#0f172a",
            wraplength=self.bubble_w - 24,
            justify="left",
            padx=8,
            pady=4
        )
        self.message_label.pack(fill="both", expand=True)

        # Interactive Command Input Bar
        input_bar = tk.Frame(self.bubble_frame, bg="#0f172a")
        input_bar.pack(fill="x", padx=6, pady=2)

        self.cmd_entry = tk.Entry(
            input_bar,
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#f1f5f9",
            insertbackground="#fbbf24",
            relief="flat",
            bd=3
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.cmd_entry.bind("<Return>", lambda e: self._on_send_command())

        send_btn = tk.Button(
            input_bar,
            text="⚔️ Run",
            font=("Segoe UI", 8, "bold"),
            bg="#b45309",          # Amber-700
            fg="#ffffff",
            activebackground="#d97706",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=self._on_send_command
        )
        send_btn.pack(side="right")

        # Quick Action Buttons Strip
        action_bar = tk.Frame(self.bubble_frame, bg="#0f172a")
        action_bar.pack(fill="x", padx=6, pady=(0, 6))

        def make_action_chip(parent, text, cmd, bg_col="#334155"):
            b = tk.Label(
                parent,
                text=text,
                font=("Segoe UI", 8),
                bg=bg_col,
                fg="#e2e8f0",
                padx=5,
                pady=2,
                cursor="hand2",
                relief="flat"
            )
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e: cmd())
            return b
        make_action_chip(action_bar, "🚶 Walk", self.toggle_walk, bg_col="#334155")
        make_action_chip(action_bar, "🎙️ Mic", self.toggle_voice_listen, bg_col="#047857")
        self.auto_listen_chip = make_action_chip(action_bar, "🎧 Auto", self.toggle_auto_listen, bg_col="#334155")
        make_action_chip(action_bar, "🎵 Music", lambda: self.prompt_action("play "), bg_col="#b45309")
        make_action_chip(action_bar, "📝 Note", lambda: self.prompt_action("create note called "), bg_col="#6d28d9")
        make_action_chip(action_bar, "🌤 Weather", lambda: self.execute_query("weather"), bg_col="#0891b2")
        make_action_chip(action_bar, "💻 Code", lambda: self.execute_query("open vscode here"), bg_col="#475569")
        make_action_chip(action_bar, "⚔️ Roar", lambda: self.execute_query("jai mahishmati"), bg_col="#991b1b")

        # Place bubble inside canvas
        self.bubble_win_id = self.canvas.create_window(
            self.win_w // 2,
            self.bubble_h // 2 + 5,
            window=self.bubble_frame,
            width=self.bubble_w,
            height=self.bubble_h,
            state="hidden"
        )

        # Mouse Interactions on Buddy Sprite
        self.canvas.tag_bind(self.char_sprite_id, "<Button-1>", self._on_click_char)
        self.canvas.tag_bind(self.char_sprite_id, "<B1-Motion>", self._on_drag_char)
        self.canvas.tag_bind(self.char_sprite_id, "<Button-3>", self._on_right_click)

        # Bind Esc to hide bubble
        self.root.bind("<Escape>", lambda e: self.hide_bubble())

        # Global keyboard shortcuts (when bubble is focused)
        self.root.bind("<Control-b>", lambda e: self._toggle_tray_visibility())
        self.root.bind("<Control-B>", lambda e: self._toggle_tray_visibility())
        self.root.bind("<Control-m>", lambda e: self._open_music_prompt())
        self.root.bind("<Control-M>", lambda e: self._open_music_prompt())
        self.root.bind("<Control-n>", lambda e: self._open_note_prompt())
        self.root.bind("<Control-N>", lambda e: self._open_note_prompt())
        self.root.bind("<Control-w>", lambda e: self.execute_query("weather"))
        self.root.bind("<Control-W>", lambda e: self.execute_query("weather"))

    def _toggle_tray_visibility(self):
        """Show/hide the Bahubali window via keyboard shortcut."""
        try:
            state = self.root.state()
            if state in ("normal", "zoomed"):
                self.root.withdraw()
            else:
                self.root.deiconify()
                self.root.focus_force()
        except Exception:
            pass

    def _open_music_prompt(self):
        self.prompt_action("play ")

    def _open_note_prompt(self):
        self.prompt_action("create note called ")

    def toggle_mute(self):
        """Toggle speech audio output."""
        self.voice_muted = not self.voice_muted
        self.mute_btn.config(text="🔇" if self.voice_muted else "🔊")
        if self.voice_muted:
            self.tts.stop()

    def _initial_greeting(self):
        """Play initial Baahubali greeting."""
        greeting = "Jai Mahishmati! Bahubali has arrived at your desktop! Command me, Antigravity, or Claude anytime!"
        self.say(greeting, state="celebrate")

    def say(self, text, state="talk", duration=None):
        """Speak via TTS, display in speech bubble, and play animation."""
        if not text:
            return

        self.show_bubble(text, duration=duration)
        self.set_state(state)
        # Speak asynchronously if not muted
        if not self.voice_muted:
            self.tts.speak(text)

    def show_bubble(self, text, duration=None):
        """Display speech bubble above Baahubali."""
        self.message_label.config(text=text)
        self.canvas.itemconfigure(self.bubble_win_id, state="normal")
        timeout = duration or self.config.get("bubble_timeout", 8)
        self.bubble_hide_time = time.time() + timeout

    def hide_bubble(self):
        """Hide speech bubble."""
        self.canvas.itemconfigure(self.bubble_win_id, state="hidden")

    def set_state(self, state):
        """Change animation state."""
        self.current_state = state
        self.sprite_mgr.set_state(state)

    def _on_speech_start(self):
        """TTS started speaking."""
        def _apply():
            self.previous_state = self.current_state
            if self.current_state not in ["celebrate", "sleep"]:
                self.set_state("talk")
        try:
            self.root.after(0, _apply)
        except Exception:
            pass

    def _on_speech_end(self):
        """TTS finished speaking."""
        def _apply():
            if self.current_state == "talk":
                self.set_state(self.previous_state if self.previous_state != "talk" else "idle")
        try:
            self.root.after(0, _apply)
        except Exception:
            pass

    def toggle_voice_listen(self):
        """Trigger microphone listening on background thread with live state updates."""
        if self.is_listening:
            return

        def _listen_worker():
            self.is_listening = True
            self.stt._stop_listening = False
            self.root.after(0, lambda: self.show_bubble("🎙️ Listening... (Speak your command now!)", duration=10))
            self.root.after(0, lambda: self.set_state("think"))

            def _on_progress(stage):
                if stage == "speech_detected":
                    self.root.after(0, lambda: self.show_bubble("🎙️ Hearing you... keep speaking!", duration=6))
                elif stage == "transcribing":
                    self.root.after(0, lambda: self.show_bubble("🧠 Recognizing your voice...", duration=6))

            recognized_text = self.stt.record_phrase(max_duration=8.5, silence_limit=1.4, progress_callback=_on_progress)
            self.is_listening = False

            if recognized_text:
                self.root.after(0, lambda: self.execute_query(recognized_text))
            else:
                self.root.after(0, lambda: self.say("I could not hear clearly. Click [🎙️ Mic] and speak closer to the microphone!", state="idle"))

        threading.Thread(target=_listen_worker, daemon=True).start()

    def toggle_auto_listen(self):
        """Toggle continuous auto-listening mode."""
        self.auto_listen_enabled = not self.auto_listen_enabled
        if hasattr(self, 'auto_listen_chip'):
            self.auto_listen_chip.config(
                text="🎧 Auto: ON" if self.auto_listen_enabled else "🎧 Auto: OFF",
                bg="#059669" if self.auto_listen_enabled else "#334155"
            )
        if self.auto_listen_enabled:
            self.say("Continuous hearing mode active! Just speak your command anytime, Commander — no wake word needed!", state="talk")
            self.stt.listen_in_background(
                on_speech_detected_callback=self._on_auto_speech_detected,
                require_wake_word=False
            )
        else:
            self.stt.stop_listening()
            self.say("Continuous hearing paused. Click [🎙️ Mic] whenever you wish to speak.", state="idle")

    def _on_auto_speech_detected(self, text):
        """Callback from background continuous listener."""
        if not text:
            return
        # Don't process if TTS is speaking (prevents mic picking up our own voice)
        if self.tts.is_speaking:
            return
        # Filter out very short noise-transcriptions (less than 2 real words)
        words = text.strip().split()
        if len(words) < 2:
            return
        self.root.after(0, lambda: self.execute_query(text))

    def test_mic_levels(self):
        """Diagnostic routine to test mic input and report to user."""
        self.show_bubble("🎤 Testing microphone... Please say something aloud for 2 seconds!", duration=5)
        def _worker():
            import sounddevice as sd
            import numpy as np
            try:
                dev = sd.query_devices(kind='input')
                sr = int(dev.get('default_samplerate', 16000))
                ch = min(2, dev.get('max_input_channels', 1))
                rec = sd.rec(int(sr * 2.0), samplerate=sr, channels=ch, dtype='int16')
                sd.wait()
                mono = rec.mean(axis=1) if ch > 1 else rec.flatten()
                peak = int(np.max(np.abs(mono)))
                rms = float(np.sqrt(np.mean(mono.astype(np.float32)**2)))
                report = f"Mic: {dev.get('name')[:25]}\nPeak level: {peak}/32767 | RMS: {rms:.1f}\n"
                if peak > 200:
                    report += "Audio hardware working great!"
                else:
                    report += "Level quiet. Auto-gain will boost signal."
                self.root.after(0, lambda: self.show_bubble(report, duration=10))
            except Exception as e:
                self.root.after(0, lambda: self.show_bubble(f"Mic test error: {e}", duration=8))
        threading.Thread(target=_worker, daemon=True).start()

    def prompt_action(self, prefix):
        """Populate input box with action prefix."""
        self.show_bubble("Enter your instructions below:")
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, prefix)
        self.cmd_entry.focus_set()

    def _on_send_command(self):
        """User typed a command in entry box and pressed Enter/Run."""
        query = self.cmd_entry.get().strip()
        if not query:
            return
        self.cmd_entry.delete(0, tk.END)
        self.execute_query(query)

    def execute_query(self, query):
        """Execute query using BuddyBrain on a worker thread to keep GUI responsive."""
        self.set_state("think")
        self.show_bubble(f"Conquering: '{query}'...", duration=20)

        def _brain_worker():
            reply, anim_state, _ = self.brain.process(query)
            self.root.after(0, lambda: self.say(reply, state=anim_state))

        threading.Thread(target=_brain_worker, daemon=True).start()

    def toggle_walk(self):
        """Toggle auto-walking along bottom edge."""
        self.auto_walk = not self.auto_walk
        if self.auto_walk:
            self.say("Marching across the borders of Mahishmati!", state="walk_right")
        else:
            self.say("Halted! Standing guard at this post.", state="idle")

    def set_motion(self, direction):
        """Direct character movement."""
        if direction == "stop":
            self.auto_walk = False
            self.set_state("idle")
        elif direction in ["left", "right"]:
            self.auto_walk = True
            self.walk_direction = direction
            self.set_state(f"walk_{direction}")

    def _on_click_char(self, event):
        """Clicking on character opens speech bubble / command input."""
        self._drag_start_x = event.x_root - self.x
        self._drag_start_y = event.y_root - self.y

        current_state = self.canvas.itemcget(self.bubble_win_id, "state")
        if current_state == "hidden":
            self.show_bubble("Jai Mahishmati! What are your orders, Commander?", duration=12)
            self.cmd_entry.focus_set()

    def _on_drag_char(self, event):
        """Drag character with mouse across desktop."""
        self.x = event.x_root - self._drag_start_x
        self.y = event.y_root - self._drag_start_y
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.x}+{self.y}")

    def _on_right_click(self, event):
        """Popup context menu."""
        menu = tk.Menu(self.root, tearoff=0, bg="#1e293b", fg="#f8fafc", activebackground="#f59e0b", activeforeground="#000000")
        menu.add_command(label="⚔️ Talk to Bahubali", command=lambda: self.show_bubble("What are your orders, Commander?"))
        menu.add_command(label="🎙️ Voice Command (Mic)", command=self.toggle_voice_listen)
        menu.add_command(label="🎧 Toggle Auto-Listen Mode", command=self.toggle_auto_listen)
        menu.add_command(label="🔬 Test Microphone Levels", command=self.test_mic_levels)
        menu.add_command(label="🎵 Play Music...", command=lambda: self.prompt_action("play "))
        menu.add_command(label="🌤 Weather...", command=lambda: self.execute_query("weather"))
        menu.add_command(label="📝 Create Note...", command=lambda: self.prompt_action("create note called "))
        menu.add_command(label="⏰ Schedule Reminder...", command=lambda: self.prompt_action("remind me in 10 minutes to "))
        menu.add_separator()
        menu.add_command(label="⚡ Run Antigravity...", command=lambda: self.prompt_action("antigravity "))
        menu.add_command(label="🤖 Claude Code in VS Code...", command=lambda: self.prompt_action("claude "))
        menu.add_command(label="💻 Open VS Code Here", command=lambda: self.execute_query("open vscode here"))
        menu.add_command(label="🌿 Git Status", command=lambda: self.execute_query("git status"))
        menu.add_command(label="📸 Take Screenshot", command=lambda: self.execute_query("take a screenshot"))
        menu.add_separator()
        menu.add_command(label="🚶 Toggle Walking", command=self.toggle_walk)
        menu.add_command(label="🔇 Toggle Voice Mute", command=self.toggle_mute)
        menu.add_command(label="🎉 Roar: Jai Mahishmati!", command=lambda: self.execute_query("jai mahishmati"))
        menu.add_command(label="🧘 Meditate (Sleep)", command=lambda: self.execute_query("sleep"))
        menu.add_separator()
        menu.add_command(label="❌ Exit Bahubali", command=self.exit_app)

        menu.tk_popup(event.x_root, event.y_root)

    def _animation_loop(self):
        """Main periodic GUI loop for walking physics & sprite frame advancing."""
        now = time.time()

        # 1. Advance Sprite Frame
        frame_path = self.sprite_mgr.advance_frame()
        if os.path.exists(frame_path):
            try:
                pil_img = Image.open(frame_path)
                self._current_tk_img = ImageTk.PhotoImage(pil_img)
                self.canvas.itemconfig(self.char_sprite_id, image=self._current_tk_img)
            except Exception:
                pass

        # 2. Auto-hide speech bubble after timeout
        if self.bubble_hide_time > 0 and now > self.bubble_hide_time and not self.cmd_entry.get().strip():
            # If entry is not actively focused, hide bubble
            if self.root.focus_get() != self.cmd_entry:
                self.hide_bubble()
                self.bubble_hide_time = 0

        # 3. Walking Physics
        if self.auto_walk and self.current_state in ["idle", "walk_left", "walk_right"]:
            if now > self.walk_pause_until:
                target_state = f"walk_{self.walk_direction}"
                if self.current_state != target_state:
                    self.set_state(target_state)

                # Move window horizontally
                step = self.walk_speed if self.walk_direction == "right" else -self.walk_speed
                self.x += step
                self.walk_step_counter += 1

                # Bounce at screen edges
                min_x = 0
                max_x = self.screen_w - self.win_w

                if self.x <= min_x:
                    self.x = min_x
                    self.walk_direction = "right"
                    self.set_state("walk_right")
                    self.walk_pause_until = now + 1.5
                elif self.x >= max_x:
                    self.x = max_x
                    self.walk_direction = "left"
                    self.set_state("walk_left")
                    self.walk_pause_until = now + 1.5

                # Occasional random warrior pause (every ~180 steps)
                if self.walk_step_counter > 180:
                    self.walk_step_counter = 0
                    self.walk_pause_until = now + 2.0
                    self.set_state("idle")

                self.root.geometry(f"{self.win_w}x{self.win_h}+{self.x}+{self.y}")

        # Schedule next frame
        self.root.after(self._tick_interval_ms, self._animation_loop)

    def _handle_ipc_message(self, msg):
        """Handle incoming CLI commands sent over IPC."""
        cmd_type = msg.get("type", "query")
        data = msg.get("data", "")

        if cmd_type == "query":
            self.root.after(0, lambda: self.execute_query(data))
            return f"Order '{data}' received by Bahubali."

        elif cmd_type == "say":
            self.root.after(0, lambda: self.say(data, state="talk"))
            return f"Bahubali is speaking: {data}"

        elif cmd_type == "state":
            self.root.after(0, lambda: self.set_state(data))
            return f"Bahubali state set to: {data}"

        elif cmd_type == "walk":
            if data in ["left", "right", "stop"]:
                self.root.after(0, lambda: self.set_motion(data))
            else:
                self.root.after(0, self.toggle_walk)
            return "Walk updated."

        elif cmd_type == "exit":
            self.root.after(100, self.exit_app)
            return "Bahubali is retreating to Mahishmati."

        return "Unknown command."

    def exit_app(self):
        """Clean shutdown."""
        try:
            log_path = os.path.expanduser("~/.duh_buddy/gui_runtime.log")
            import traceback
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[exit_app called at {time.ctime()}]\n")
                traceback.print_stack(file=f)
        except Exception:
            pass
        try:
            self.ipc_server.stop()
            self.tts.stop()
            self.brain.reminders.stop()
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        """Start Tkinter main event loop."""
        self.root.mainloop()


def launch_gui():
    log_path = os.path.expanduser("~/.duh_buddy/gui_runtime.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[Starting GUI at {time.ctime()}]\n")
        app = DesktopBuddyGUI()
        # Start system tray + global hotkey (Ctrl+Alt+B toggles Bahubali)
        if app.tray:
            app.tray.start()
        app.run()
    except BaseException as e:
        import traceback
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[GUI EXITED/CRASH] {type(e).__name__}: {e}\n")
            traceback.print_exc(file=f)


if __name__ == "__main__":
    launch_gui()
