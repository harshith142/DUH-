"""
Speech-to-Text (STT) Engine for Desktop Buddy Bahubali — The Whisper of Mahishmati.
 
Strategy (in priority order):
  1. OpenAI Whisper (offline, fastest, no network)  ← PRIMARY
  2. Google Speech API via SpeechRecognition (online fallback)
  3. Windows SAPI SpInProcRecognizer (native fallback)

Audio capture: sounddevice (bypasses PyAudio dependency)
Writes temp WAV to disk (avoids [WinError 50] BytesIO WASAPI bug)
"""

import os
import io
import wave
import time
import tempfile
import threading
import numpy as np
import sounddevice as sd

LOG_FILE = os.path.expanduser("~/.duh_buddy/voice.log")

# ── Whisper model (loaded once, lazily) ───────────────────────────────────────
_whisper_model = None
_whisper_lock = threading.Lock()


def _get_whisper(model_name="base"):
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            try:
                import whisper
                log_voice(f"Loading Whisper '{model_name}' model (first run may take ~10-20s)...")
                _whisper_model = whisper.load_model(model_name)
                log_voice("Whisper model loaded ✓")
            except ImportError:
                log_voice("Whisper not installed — will use Google STT fallback")
                _whisper_model = None
            except Exception as e:
                log_voice(f"Whisper load error: {e}")
                _whisper_model = None
    return _whisper_model


def log_voice(msg):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def resample_to_16k(audio, orig_sr):
    """Fast linear resample of audio array to 16000 Hz for STT engines."""
    if orig_sr == 16000 or len(audio) == 0:
        return audio
    num_samples = int(len(audio) * 16000 / orig_sr)
    old_indices = np.linspace(0, len(audio) - 1, len(audio))
    new_indices = np.linspace(0, len(audio) - 1, num_samples)
    return np.interp(new_indices, old_indices, audio).astype(audio.dtype)


def _write_wav_file(audio_int16, sample_rate, path):
    """Write int16 mono audio array to WAV file at path."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


def _transcribe_with_whisper(audio_int16, sample_rate):
    """Transcribe audio array using Whisper (offline, in-memory, no ffmpeg required)."""
    model = _get_whisper()
    if model is None:
        return None
    try:
        # Convert int16 to float32 normalized to [-1, 1]
        audio_float = audio_int16.astype(np.float32) / 32768.0
        result = model.transcribe(
            audio_float,
            fp16=False,
            temperature=(0.0, 0.2, 0.4),
            no_speech_threshold=0.45,
            logprob_threshold=-1.2,
            compression_ratio_threshold=2.4,
            condition_on_previous_text=False
        )
        text = result.get("text", "").strip()
        log_voice(f"Whisper transcribed: '{text}'")
        return text if text else None
    except Exception as e:
        log_voice(f"Whisper transcription error: {e}")
        return None


def _transcribe_with_google(audio_int16):
    """
    Fallback: Google Speech REST API called directly via requests with raw PCM bytes.
    Bypasses speech_recognition's waveIn sink (avoids [WinError 50]) and sends raw PCM
    (avoids WAV header corruption in audio/l16).
    """
    try:
        import requests
        import json
        url = (
            "https://www.google.com/speech-api/v2/recognize"
            "?output=json&lang=en-IN&key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        )
        raw_pcm = audio_int16.tobytes()
        resp = requests.post(
            url,
            data=raw_pcm,
            headers={"Content-Type": "audio/l16; rate=16000"},
            timeout=10
        )
        lines = [l.strip() for l in resp.text.strip().splitlines() if l.strip()]
        for line in reversed(lines):
            try:
                obj = json.loads(line)
                alts = obj.get("result", [{}])[0].get("alternative", [])
                if alts:
                    text = alts[0].get("transcript", "").strip()
                    if text:
                        log_voice(f"Google STT transcribed: '{text}'")
                        return text
            except Exception:
                continue
        log_voice("Google STT: no transcript in response")
        return None
    except Exception as e:
        log_voice(f"Google STT error: {e}")
        return None


class STTEngine:
    def __init__(self, sample_rate=16000, energy_threshold=500, whisper_model="base", wake_words=None):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.whisper_model = whisper_model
        self.is_listening = False
        self._stop_listening = False
        self.listener_thread = None
        self.wake_words = wake_words or ["hey bahubali", "bahubali", "hey baahubali", "baahubali", "hey buddy"]
        # Pre-load Whisper model in background so first call is fast
        threading.Thread(target=_get_whisper, args=(whisper_model,), daemon=True).start()

    def record_phrase(self, max_duration=9.0, silence_limit=1.5, progress_callback=None):
        """
        Capture voice from mic with ambient noise calibration + AGC.
        Returns transcribed string or None.
        """
        self._stop_listening = False
        chunk_duration = 0.1          # 100ms chunks
        chunk_samples = int(self.sample_rate * chunk_duration)
        recorded_frames = []
        silence_duration = 0.0
        speech_started = False
        start_time = time.time()

        try:
            # Find MME input device on Windows to avoid WASAPI WinError 50
            import platform
            input_device = None
            if platform.system() == 'Windows':
                devices = sd.query_devices()
                # First, try to get the default input device (which is usually the actual microphone)
                default_input = sd.query_devices(kind='input')
                default_hostapi = sd.query_hostapis(default_input['hostapi'])
                if default_hostapi['name'] == 'MME' and default_input.get('max_input_channels', 0) > 0:
                    input_device = default_input['index']
                    log_voice(f"Using default MME input device: {input_device} ({default_input['name']})")
                else:
                    # Fallback: find first MME device that's not "Sound Mapper"
                    for i, dev in enumerate(devices):
                        api = sd.query_hostapis(dev['hostapi'])
                        if api['name'] == 'MME' and dev['max_input_channels'] > 0 and 'Sound Mapper' not in dev['name']:
                            input_device = i
                            log_voice(f"Using MME input device: {input_device} ({dev['name']})")
                            break
                    # Last resort: any MME input device
                    if input_device is None:
                        for i, dev in enumerate(devices):
                            api = sd.query_hostapis(dev['hostapi'])
                            if api['name'] == 'MME' and dev['max_input_channels'] > 0:
                                input_device = i
                                log_voice(f"Using fallback MME input device: {input_device} ({dev['name']})")
                                break

            # Get device info for channel count & native hardware sample rate
            if input_device is not None:
                dev_info = sd.query_devices(input_device, 'input')
            else:
                dev_info = sd.query_devices(kind='input')

            channels = min(2, int(dev_info.get('max_input_channels', 1)))
            native_rate = int(dev_info.get('default_samplerate', 44100))
            chunk_samples = int(native_rate * chunk_duration)

            # ── Phase 1: Ambient calibration (0.3s) ──────────────────────────
            ambient_frames = []
            stream_kwargs = {
                'samplerate': native_rate,
                'channels': channels,
                'dtype': 'int16'
            }
            if input_device is not None:
                stream_kwargs['device'] = input_device

            with sd.InputStream(**stream_kwargs) as stream:
                for _ in range(3):
                    data, _ = stream.read(chunk_samples)
                    ambient_frames.append(data.copy())

                ambient_arr = np.concatenate(ambient_frames, axis=0)
                ambient_mono = ambient_arr.mean(axis=1) if channels > 1 else ambient_arr.flatten()
                ambient_rms = float(np.sqrt(np.mean(ambient_mono.astype(np.float32) ** 2)))
                # Lower minimum threshold for quiet microphones
                speech_threshold = max(0.5, ambient_rms * 2.2)
                log_voice(f"Ambient RMS: {ambient_rms:.2f}, Threshold: {speech_threshold:.2f} (native SR: {native_rate})")

                # ── Phase 2: Dynamic recording loop ──────────────────────────
                while time.time() - start_time < max_duration and not self._stop_listening:
                    data, _ = stream.read(chunk_samples)
                    recorded_frames.append(data.copy())

                    mono_chunk = data.mean(axis=1) if channels > 1 else data.flatten()
                    chunk_rms = float(np.sqrt(np.mean(mono_chunk.astype(np.float32) ** 2)))

                    if chunk_rms > speech_threshold:
                        if not speech_started:
                            speech_started = True
                            log_voice(f"Speech detected (RMS: {chunk_rms:.2f})")
                            if progress_callback:
                                progress_callback("speech_detected")
                        silence_duration = 0.0
                    elif speech_started:
                        silence_duration += chunk_duration
                        if silence_duration >= silence_limit:
                            log_voice(f"Silence limit ({silence_duration:.1f}s), done capturing.")
                            break

            if not recorded_frames:
                log_voice("No audio frames captured.")
                return None

            if not speech_started:
                log_voice("No speech detected above threshold.")
                return None

            # ── Phase 3: Mono + Resample to 16kHz + AGC ───────────────────────
            raw_array = np.concatenate(recorded_frames, axis=0)
            mono_audio = raw_array.mean(axis=1) if channels > 1 else raw_array.flatten()

            if native_rate != 16000:
                mono_audio = resample_to_16k(mono_audio, native_rate)

            peak = float(np.max(np.abs(mono_audio)))
            duration = len(mono_audio) / 16000
            log_voice(f"Captured: {duration:.1f}s, peak={peak:.0f}")

            if peak > 0 and peak < 20000:
                gain = min(6.0, 16000.0 / max(1.0, peak))
                mono_audio = np.clip(
                    mono_audio.astype(np.float32) * gain, -32768, 32767
                ).astype(np.int16)
                log_voice(f"AGC boost {gain:.2f}x → peak={np.max(np.abs(mono_audio)):.0f}")
            else:
                mono_audio = mono_audio.astype(np.int16)

            # ── Phase 4: Transcribe (Whisper offline + Google REST fallback) ───
            if progress_callback:
                progress_callback("transcribing")

            # Try Whisper first (offline, high accuracy)
            text = _transcribe_with_whisper(mono_audio, self.sample_rate)

            # Fallback to Google STT if Whisper returned no text
            if not text:
                text = _transcribe_with_google(mono_audio)

            return text

        except Exception as e:
            log_voice(f"STT fatal error: {e}")
            return None

    def listen_in_background(self, on_speech_detected_callback, require_wake_word=True):
        """Start a continuous background listening loop with optional wake word detection."""
        if self.is_listening:
            return
        self.is_listening = True
        self._stop_listening = False

        def loop():
            log_voice("Continuous listener started (Mahishmati ears open - waiting for wake word).")
            while self.is_listening and not self._stop_listening:
                text = self.record_phrase(max_duration=7.0, silence_limit=1.2)
                if text and self.is_listening:
                    if require_wake_word:
                        # Check for wake word
                        command = self._extract_command_after_wake_word(text)
                        if command:
                            log_voice(f"Wake word detected! Command: '{command}'")
                            on_speech_detected_callback(command)
                        else:
                            log_voice(f"No wake word in: '{text}' - ignoring")
                    else:
                        # No wake word required — pass everything through
                        log_voice(f"Auto-listen (no wake word required): '{text}'")
                        on_speech_detected_callback(text)
                time.sleep(0.2)
            log_voice("Continuous listener stopped.")

        self.listener_thread = threading.Thread(target=loop, daemon=True)
        self.listener_thread.start()

    def _extract_command_after_wake_word(self, text):
        """Check if text contains a wake word and return the command after it."""
        import re
        text_lower = text.lower().strip()
        for wake_word in self.wake_words:
            # Create regex pattern to match wake word as whole word(s)
            # Escape special regex chars and allow word boundaries
            pattern = r'(^|[\s,]+)' + re.escape(wake_word) + r'([\s,]+|$)'
            match = re.search(pattern, text_lower)
            if match:
                # Get everything after the wake word
                end_pos = match.end()
                command = text_lower[end_pos:].strip()
                # Remove leading commas, "to", etc. - use removeprefix for exact string matching
                for prefix in [", ", ",", ". ", ".", "to ", "to"]:
                    if command.startswith(prefix):
                        command = command[len(prefix):].strip()
                        break
                return command if command else None
        return None

    def stop_listening(self):
        self.is_listening = False
        self._stop_listening = True


if __name__ == "__main__":
    print("🎙️ Bahubali STT Test — speak after the prompt")
    stt = STTEngine()
    time.sleep(1)  # let Whisper load

    print("Recording for up to 8s... SPEAK NOW:")
    result = stt.record_phrase(
        max_duration=8.0,
        progress_callback=lambda s: print(f"  [{s}]")
    )
    print(f"\nTranscribed: {result!r}")
