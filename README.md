# ⚔️ DUH: The Baahubali Desktop Companion & AI Assistant

An animated, heroic, voice-enabled desktop companion designed to run autonomously on Windows. DUH appears as **Baahubali** walking gracefully above your taskbar, equipped with full system automation, scheduled task reminders, local offline LLM reasoning via **Ollama (Llama 3.2)**, and autonomous coding delegation via **Google Antigravity CLI** and **Anthropic Claude Code in VS Code**.

---

## 🌟 Key Features

1. **Heroic Baahubali Desktop Companion**:
   - High-detail custom pixel-vector animated warrior with royal golden armor (*Kavacham*), crimson dhoti with gold trim, flowing black warrior locks with topknot, forehead *Tilak*, and the legendary Mahishmati royal broadsword.
   - Transparent, frameless, always-on-top desktop window walking smoothly above your Windows taskbar.
   - States: `idle`, `walk_left`, `walk_right`, `think`, `talk`, `celebrate` (sword raised with divine golden lightning bursts and victory roar!), `sleep` (warrior *Padmasana* meditation).
   - Fully interactive: drag anywhere with mouse, left-click to open command hub, right-click context menu.

2. **System Tray & Global Hotkey**:
   - Bahubali lives in the Windows system tray (notification area) — right-click for quick actions.
   - **Ctrl+Alt+B** toggles Bahubali show/hide from anywhere, even when hidden.
   - Keyboard shortcuts: `Ctrl+B` toggle, `Ctrl+M` music prompt, `Ctrl+N` note prompt, `Ctrl+W` weather.

3. **Multi-Model LLM Intelligence**:
   - **Offline Local LLM (Ollama Llama 3.2)**: 100% private, zero-latency conversational intelligence, algorithm design, and technical reasoning without cloud dependence.
   - **Google Antigravity CLI (`agy`)**: Autonomous coding agent capable of multi-file software engineering, testing, and full project implementations.
   - **Anthropic Claude Code (`claude`)**: Direct terminal integration and launch inside Microsoft VS Code.

4. **Natural Language Task Reminders & Scheduling**:
   - "Remind me in 10 minutes to review code"
   - "Remind me at 5:30 PM to commit changes"
   - "List my reminders" / "Clear all reminders"
   - Automatically speaks the alert when due and pops up an alert speech bubble!

5. **Full-Duplex Voice Assistance**:
   - **Speech-to-Text (STT)**: Microphone recording with dynamic silence detection and speech recognition.
   - **Text-to-Speech (TTS)**: Offline Windows SAPI5 audio engine synchronized with Baahubali's talking mouth animation.
   - Speech mute toggle available directly in the bubble header.

6. **Windows Desktop & Computer Automation**:
   - **Music**: Apple Music (`play believer in apple music`), Spotify (`play taylor swift on spotify`), local music files (`play local music`), resume/pause/next/prev.
   - **Launch applications** (`open chrome`, `open vscode`, `launch spotify`, `open calculator`, etc.).
   - **Volume & media playback** (`volume up`, `volume down`, `mute`, `next song`, `pause music`).
   - **Brightness control** (`set brightness to 50`, `what is brightness`).
   - **Desktop notifications** (`show notification hello world`).
   - **Folder navigation** (`open downloads`, `open documents`, `open desktop`).
   - **Sticky notes** (`create note called meeting ideas`).
   - **Weather** (`weather`, `weather in london`).
   - **Process control** (`kill chrome`, `list processes`, `empty recycle bin`).
   - Workstation lock (`lock screen`) & instant screenshots (`take screenshot`).
   - Hardware diagnostics (`battery`, `cpu`, `ram`, `system stats`).
   - Web searches on Google & YouTube.

7. **Permissions, Safety & Auditability**:
   - Permission management engine (`permissions.json`) ensuring user data access is explicit and controlled.
   - Immutable activity audit log stored at `~/.duh_buddy/activity.log`.

8. **Universal CLI Compliance**:
   - Available globally from any command line via `duh`:
     ```bash
     duh start                    # Summon Baahubali to desktop
     duh "open vscode"            # Send natural language task
     duh "remind me in 15m to ..."# Set scheduled reminder
     duh say "Jai Mahishmati"     # Speak message aloud
     duh state celebrate          # Trigger victory roar animation
     duh walk left|right|stop     # Command movement
     duh status                   # Check online/offline status
     duh stop                     # Dismiss companion
     duh "play believer in apple music"  # Play music
     duh "weather"                # Check weather
     duh "create note called ideas"      # Create sticky note
     ```

---

## 🚀 Quick Start Guide

### 1. Launch DUH
From PowerShell, CMD, or VS Code terminal:
```bash
duh start
```
*Baahubali will appear above your taskbar, speak a royal greeting, and begin his patrol.*

### 2. Voice Commands
Click the `[🎙️ Mic]` button on the speech bubble (or chant *"Hey DUH"*) and speak:
- *"Open VS Code here"*
- *"Ask Antigravity to write a Python script"*
- *"Ask Claude to explain this function"*
- *"Remind me in 20 minutes to commit my code"*
- *"Turn the volume up"*
- *"Take a screenshot"*
- *"Jai Mahishmati!"*

### 3. Quick Action Chips
Click directly on Baahubali to open the Command Hub with quick-action buttons:
- `[🎙️ Mic]`: Activate voice listening
- `[⚡ Antigravity]`: Prompt autonomous software agent
- `[🤖 Claude]`: Prompt Claude Code in VS Code
- `[⏰ Remind]`: Fast-schedule a reminder
- `[💻 Code]`: Open VS Code in current workspace
- `[⚔️ Roar]`: Trigger "Jai Mahishmati!" victory sword celebration
- `[🚶 Walk]`: Toggle autonomous walking along the bottom edge

---

## 🏰 Project Architecture

```
DUH/
├── duh.py                   # Main CLI controller & daemon launcher
├── duh.cmd                  # Windows batch launcher (globally in PATH)
├── README.md                # Comprehensive documentation
└── buddy_core/
    ├── sprites.py           # 38-frame procedural Baahubali sprite generator
    ├── gui.py               # Transparent Tkinter GUI & animation loop
    ├── brain.py             # NLP Intent classifier & Mahishmati router
    ├── llm.py               # Local Ollama (Llama 3.2) reasoning engine
    ├── reminders.py         # Persistent task reminder & timer scheduler
    ├── coding_assistant.py  # Git helper, file scanner, code advisor
    ├── agents.py            # Antigravity CLI & Claude Code integrations
    ├── executor.py          # Windows OS automation (apps, audio, screen)
    ├── permissions.py       # Permission manager & immutable activity log
    ├── tts.py               # Windows SAPI5 voice speech engine
    ├── stt.py               # Sounddevice microphone voice recognition
    ├── ipc.py               # Local loopback TCP server for instant CLI control
    ├── config.py            # Configuration loader (~/.duh_buddy/config.json)
    └── assets/              # 38 high-res Baahubali sprite PNG frames
```

---

*Mahishmati Saamrajyam Amar Rahe!* ⚔️
