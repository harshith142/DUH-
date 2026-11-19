"""
Task Reminder & Scheduling Engine for Bahubali Desktop Buddy.
Supports natural language scheduling:
- "remind me in 10 minutes to test my code"
- "remind me to commit changes in 1 hour"
- "in 30 seconds remind me to stretch"
- "remind me at 17:30 to join meeting"
- "remind me at 5:30 pm to review PR"
Stores reminders persistently in ~/.duh_buddy/reminders.json.
Runs a background scheduler thread that notifies the GUI/TTS when due.
"""

import os
import re
import json
import time
import threading
from datetime import datetime, timedelta

REMINDERS_FILE = os.path.expanduser("~/.duh_buddy/reminders.json")


class ReminderManager:
    def __init__(self, on_trigger_callback=None):
        self.on_trigger = on_trigger_callback
        self.reminders = []
        self._lock = threading.Lock()
        self._running = True
        self.load()

        # Start background timer check
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()

    def set_callback(self, callback):
        self.on_trigger = callback

    def load(self):
        """Load pending reminders from disk."""
        if os.path.exists(REMINDERS_FILE):
            try:
                with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                    self.reminders = json.load(f)
            except Exception:
                self.reminders = []

    def save(self):
        """Save pending reminders to disk."""
        os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)
        try:
            with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"[Reminder Save Error] {e}")

    def add_reminder(self, text, trigger_epoch, raw_spec=""):
        """Add a new scheduled reminder."""
        with self._lock:
            rem = {
                "id": int(time.time() * 1000),
                "text": text,
                "trigger_epoch": trigger_epoch,
                "trigger_str": datetime.fromtimestamp(trigger_epoch).strftime("%I:%M %p, %b %d"),
                "raw_spec": raw_spec,
                "created_at": time.time()
            }
            self.reminders.append(rem)
            self.reminders.sort(key=lambda x: x["trigger_epoch"])
            self.save()
            return rem

    def list_pending(self):
        """Return list of active pending reminders."""
        with self._lock:
            now = time.time()
            return [r for r in self.reminders if r["trigger_epoch"] > now]

    def remove_reminder(self, reminder_id):
        """Cancel a reminder by ID."""
        with self._lock:
            self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
            self.save()

    def clear_all(self):
        """Cancel all pending reminders."""
        with self._lock:
            self.reminders = []
            self.save()

    def parse_and_schedule(self, query):
        """
        Parses natural language queries like:
        - "remind me in 15 minutes to call Bob"
        - "remind me to push code in 2 hours"
        - "in 30 seconds remind me to stretch"
        - "remind me at 17:30 to join meeting"
        - "remind me at 5:30 pm to review PR"
        Returns (success: bool, reply_message: str, rem_obj: dict or None)
        """
        q = query.lower().strip()
        now = datetime.now()

        qty, unit, task = None, None, None

        # Pattern 1: "remind me in X minutes to Y"
        m1 = re.search(r'remind\s+(?:me\s+)?in\s+(\d+)\s*(sec|second|seconds|min|minute|minutes|hr|hour|hours)\s+(?:to\s+)?(.*)', q, re.IGNORECASE)
        if m1:
            qty = int(m1.group(1))
            unit = m1.group(2).lower()
            task = m1.group(3).strip()

        # Pattern 2: "remind me to Y in X minutes"
        if not qty:
            m2 = re.search(r'remind\s+(?:me\s+)?(?:to\s+)?(.*?)\s+in\s+(\d+)\s*(sec|second|seconds|min|minute|minutes|hr|hour|hours)', q, re.IGNORECASE)
            if m2:
                qty = int(m2.group(2))
                unit = m2.group(3).lower()
                task = m2.group(1).strip()

        # Pattern 3: "in X minutes remind me to Y"
        if not qty:
            m3 = re.search(r'in\s+(\d+)\s*(sec|second|seconds|min|minute|minutes|hr|hour|hours)\s+(?:remind\s+(?:me\s+)?(?:to\s+)?)(.*)', q, re.IGNORECASE)
            if m3:
                qty = int(m3.group(1))
                unit = m3.group(2).lower()
                task = m3.group(3).strip()

        if qty and unit:
            task = re.sub(r'^(to\s+)', '', (task or "Task reminder")).strip()
            if not task:
                task = "Task reminder"

            if "sec" in unit:
                target_dt = now + timedelta(seconds=qty)
                spec_str = f"{qty} second{'s' if qty != 1 else ''}"
            elif "min" in unit:
                target_dt = now + timedelta(minutes=qty)
                spec_str = f"{qty} minute{'s' if qty != 1 else ''}"
            else:
                target_dt = now + timedelta(hours=qty)
                spec_str = f"{qty} hour{'s' if qty != 1 else ''}"

            epoch = target_dt.timestamp()
            rem = self.add_reminder(task, epoch, raw_spec=spec_str)
            friendly_time = target_dt.strftime("%I:%M %p")
            return (
                True,
                f"Reminder set! I shall alert you in {spec_str} (at {friendly_time}) to: {task}!",
                rem
            )

        # Pattern 4: "remind me at HH:MM [am/pm] to Y"
        m_at1 = re.search(r'remind\s+(?:me\s+)?at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+(?:to\s+)?(.*)', q, re.IGNORECASE)
        # Pattern 5: "remind me to Y at HH:MM [am/pm]"
        m_at2 = re.search(r'remind\s+(?:me\s+)?(?:to\s+)?(.*?)\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', q, re.IGNORECASE)

        m_at = m_at1 or m_at2
        if m_at:
            if m_at1:
                hour = int(m_at1.group(1))
                minute = int(m_at1.group(2) or 0)
                ampm = (m_at1.group(3) or "").lower()
                task = m_at1.group(4).strip()
            else:
                task = m_at2.group(1).strip()
                hour = int(m_at2.group(2))
                minute = int(m_at2.group(3) or 0)
                ampm = (m_at2.group(4) or "").lower()

            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += timedelta(days=1)

            task = re.sub(r'^(to\s+)', '', task).strip()
            if not task:
                task = "Task reminder"

            epoch = target_dt.timestamp()
            rem = self.add_reminder(task, epoch, raw_spec=f"at {target_dt.strftime('%I:%M %p')}")
            return (
                True,
                f"By royal decree, I will remind you at {target_dt.strftime('%I:%M %p')} to: {task}!",
                rem
            )

        return (
            False,
            "Could not parse the reminder time. Try: 'Remind me in 15 minutes to test code' or 'Remind me at 5:00 PM to review PR'.",
            None
        )

    def _scheduler_loop(self):
        """Periodic background check for due reminders."""
        while self._running:
            time.sleep(2.0)
            now = time.time()
            triggered = []

            with self._lock:
                remaining = []
                for r in self.reminders:
                    if r["trigger_epoch"] <= now:
                        triggered.append(r)
                    else:
                        remaining.append(r)

                if triggered:
                    self.reminders = remaining
                    self.save()

            for rem in triggered:
                if self.on_trigger:
                    try:
                        self.on_trigger(rem)
                    except Exception as e:
                        print(f"[Reminder Trigger Callback Error] {e}")

    def stop(self):
        self._running = False
