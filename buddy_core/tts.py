"""
Text-to-Speech (TTS) Engine for Desktop Buddy.
Powered by native Windows SAPI5 with asynchronous queue and speech event callbacks.
Zero cloud lag, 100% offline and instant.
"""

import threading
import queue
import time
import win32com.client
import pythoncom


class TTSEngine:
    def __init__(self, voice_idx=1, rate=1, volume=100):
        self.voice_idx = voice_idx  # 0: David, 1: Zira (default to clear female/ai voice if available)
        self.rate = rate
        self.volume = volume
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self._running = True
        self.on_start_callback = None
        self.on_end_callback = None

        # Start background worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def set_callbacks(self, on_start=None, on_end=None):
        self.on_start_callback = on_start
        self.on_end_callback = on_end

    def speak(self, text, block=False):
        """Enqueue text to be spoken."""
        if not text or not text.strip():
            return
        # Clean markdown/code symbols that sound weird in TTS
        clean_text = self._clean_for_speech(text)
        self.speech_queue.put(clean_text)
        if block:
            while not self.speech_queue.empty() or self.is_speaking:
                time.sleep(0.05)

    def stop(self):
        """Stop current speech and clear queue."""
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
        self.is_speaking = False

    def _clean_for_speech(self, text):
        import re
        # Strip code blocks
        text = re.sub(r'```.*?```', 'code block omitted', text, flags=re.DOTALL)
        # Strip inline code
        text = re.sub(r'`(.*?)`', r'\1', text)
        # Strip markdown links [title](url) -> title
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Strip markdown symbols like #, *, >, etc.
        text = re.sub(r'[*#_~>]', '', text)
        return text.strip()

    def _process_queue(self):
        # Initialize COM in this background thread
        pythoncom.CoInitialize()
        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            voices = speaker.GetVoices()
            if voices.Count > self.voice_idx:
                speaker.Voice = voices.Item(self.voice_idx)
            speaker.Rate = self.rate
            speaker.Volume = self.volume

            while self._running:
                try:
                    text = self.speech_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                self.is_speaking = True
                if self.on_start_callback:
                    try:
                        self.on_start_callback(text)
                    except Exception:
                        pass

                try:
                    # Speak synchronously in this worker thread (so other queue items wait)
                    # Flag 0 = Synchronous speech in worker
                    speaker.Speak(text, 0)
                except Exception as e:
                    print(f"[TTS Error] {e}")

                self.is_speaking = False
                if self.on_end_callback:
                    try:
                        self.on_end_callback()
                    except Exception:
                        pass
                self.speech_queue.task_done()
        finally:
            pythoncom.CoUninitialize()


if __name__ == "__main__":
    print("Testing TTS Engine...")
    engine = TTSEngine()
    engine.speak("Hello there! I am your new desktop buddy. Ready to help you code and manage your computer!", block=True)
    print("TTS test completed!")
