#!/usr/bin/env python3
"""Standalone Raspberry Pi cooking assistant for Lab 3.

GPIO 23 starts or restarts the interaction. GPIO 24 ends it. After starting,
the participant controls the complete recipe by speaking to the Pi.
"""

from __future__ import annotations

import argparse
import difflib
import re
import threading
import time
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel
from piper import PiperVoice


SAMPLE_RATE = 16000
ROOT = Path(__file__).resolve().parent
LAB_DIR = ROOT.parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"


SCENES: dict[str, dict[str, Any]] = {
    "idle": {
        "title": "Cooking Assistant", "body": "Press the START button to begin.",
        "commands": [],
    },
    "ask_recipe": {
        "title": "Choose a recipe", "body": "Tomato pasta\nSteak",
        "commands": ["Tomato pasta", "Steak", "Stop"],
        "say": "Hi Yan! What would you like to cook today?",
    },
    "pasta_ingredients": {
        "title": "Tomato pasta", "subtitle": "Ingredients",
        "body": "Pasta • tomato sauce • garlic • olive oil • salt • water",
        "commands": ["Start cooking", "Repeat", "Go back", "Stop"],
        "say": (
            "You will need pasta, tomato sauce, garlic, olive oil, salt, and water. "
            "Say repeat to hear the ingredients again, or say start cooking when you are ready."
        ),
    },
    "pasta_step_1": {
        "title": "Tomato pasta", "subtitle": "Step 1",
        "body": "Fill a pot with water, add salt, and bring it to a boil.",
        "commands": ["Next", "Repeat", "Go back", "Stop"],
        "say": (
            "Step one. Fill a pot with water, add salt, and place it on the stove. "
            "Say next when the water begins to boil, or say repeat to hear this step again."
        ),
    },
    "pasta_step_2": {
        "title": "Tomato pasta", "subtitle": "Step 2",
        "body": "Add the pasta, then say the cooking time.",
        "commands": ["Say minutes or seconds", "Repeat", "Go back", "Stop"],
        "say": "Step two. Add the pasta to the pot. How much time would you like to set for the pasta?",
    },
    "pasta_finish": {
        "title": "Tomato pasta", "subtitle": "Step 3",
        "body": "Check the pasta, drain it, and mix it with the tomato sauce.",
        "commands": ["Next", "Add time", "Repeat", "Stop"],
        "say": (
            "Yan, your timer is finished. Check the pasta. If it is ready, drain it and mix it "
            "with the tomato sauce. Say next when you are done, add time if it needs longer, "
            "or repeat to hear this step again."
        ),
    },
    "pasta_done": {
        "title": "Pasta ready", "body": "Enjoy your meal!",
        "commands": [],
        "say": "Your tomato pasta is ready. Enjoy your meal!",
    },
    "steak_ingredients": {
        "title": "Steak", "subtitle": "Ingredients",
        "body": "Steak • oil • salt • pepper • pan • tongs • thermometer",
        "commands": ["Start cooking", "Repeat", "Go back", "Stop"],
        "say": (
            "You will need a steak, cooking oil, salt, pepper, a frying pan, tongs, and a food "
            "thermometer. Say repeat to hear the list again, or say start cooking when you are ready."
        ),
    },
    "steak_step_1": {
        "title": "Steak", "subtitle": "Step 1",
        "body": "Pat the steak dry and season both sides.",
        "commands": ["Next", "Repeat", "Go back", "Stop"],
        "say": (
            "Step one. Pat the steak dry and season both sides with salt and pepper. "
            "Say next when you are ready, or say repeat to hear this step again."
        ),
    },
    "steak_step_2": {
        "title": "Steak", "subtitle": "Step 2",
        "body": "Heat the pan and add a little oil.",
        "commands": ["Next", "Repeat", "Go back", "Stop"],
        "say": (
            "Step two. Heat your frying pan and add a little cooking oil. Say next when the pan "
            "is hot, or say repeat to hear this step again."
        ),
    },
    "steak_step_3": {
        "title": "Steak", "subtitle": "Step 3",
        "body": "Place the steak in the pan and say a cooking time.",
        "commands": ["Say minutes or seconds", "Repeat", "Go back", "Stop"],
        "say": (
            "Step three. Carefully place the steak in the pan. How much time would you like "
            "to set before checking the first side?"
        ),
    },
    "steak_flip": {
        "title": "Steak", "subtitle": "Step 4",
        "body": "Check the crust and flip the steak.",
        "commands": ["Next", "Repeat", "Go back", "Stop"],
        "say": (
            "Yan, your timer is finished. Check the crust and flip the steak. Say next once you "
            "have turned it, or say repeat to hear this step again."
        ),
    },
    "steak_second_side": {
        "title": "Steak", "subtitle": "Second side",
        "body": "Say a cooking time for the second side.",
        "commands": ["Say minutes or seconds", "Repeat", "Go back", "Stop"],
        "say": "How much time would you like to set before checking the second side?",
    },
    "steak_temperature": {
        "title": "Steak", "subtitle": "Step 5",
        "body": "Check for at least 145°F / 63°C, then transfer it to a plate.",
        "commands": ["Start resting", "Add time", "Repeat", "Stop"],
        "say": (
            "Yan, your timer is finished. Check the center of the steak with your thermometer. "
            "Once it reaches at least 145 degrees Fahrenheit, or 63 degrees Celsius, transfer it "
            "to a plate. Say start resting when it is on the plate, add time if it needs more "
            "cooking, or repeat to hear this step again."
        ),
    },
    "steak_done": {
        "title": "Steak ready", "body": "Enjoy your meal!",
        "commands": [],
        "say": "Yan, the resting time is finished. Your steak is ready to serve. Enjoy your meal!",
    },
    "stopped": {
        "title": "Recipe stopped",
        "body": "Press the START button when you want to begin again.",
        "commands": [],
        "say": "Okay. I have stopped the recipe.",
    },
}


NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60,
}


def extract_number(text: str) -> int | None:
    match = re.search(r"\b([1-9][0-9]{0,3})\b", text)
    if match:
        return int(match.group(1))
    words = re.findall(r"[a-z]+", text.lower())
    for index, word in enumerate(words):
        if word not in NUMBER_WORDS:
            continue
        value = NUMBER_WORDS[word]
        if value >= 20 and index + 1 < len(words) and words[index + 1] in NUMBER_WORDS:
            ones = NUMBER_WORDS[words[index + 1]]
            if ones < 10:
                value += ones
        return value
    return None


def extract_duration(text: str) -> tuple[int, str] | None:
    """Return duration in seconds and a natural confirmation phrase."""
    value = extract_number(text)
    if value is None:
        return None
    lowered = text.lower()
    if "second" in lowered or re.search(r"\bsecs?\b", lowered):
        unit = "second" if value == 1 else "seconds"
        return value, f"{value} {unit}"
    unit = "minute" if value == 1 else "minutes"
    return value * 60, f"{value} {unit}"


def format_duration(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def detect_recipe(text: str) -> str | None:
    """Return a recipe from a short utterance, tolerating common ASR spellings."""
    words = re.findall(r"[a-z]+", text.lower())
    for word in words:
        if word in {"pasta", "pastor"} or difflib.SequenceMatcher(None, word, "pasta").ratio() >= 0.78:
            return "pasta"
        if word in {"steak", "stake"} or difflib.SequenceMatcher(None, word, "steak").ratio() >= 0.78:
            return "steak"
    return None


class MiniPiTFT:
    """Lab 2 MiniPiTFT display and its built-in active-low buttons."""

    def __init__(self, assistant: "Assistant") -> None:
        self.available = False
        try:
            import board
            import digitalio
            import adafruit_rgb_display.st7789 as st7789
            from PIL import Image, ImageDraw, ImageFont

            self.Image = Image
            self.ImageDraw = ImageDraw
            self.cs = digitalio.DigitalInOut(board.D5)
            self.dc = digitalio.DigitalInOut(board.D25)
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output(value=True)
            self.button_a = digitalio.DigitalInOut(board.D23)
            self.button_b = digitalio.DigitalInOut(board.D24)
            self.button_a.switch_to_input(pull=digitalio.Pull.UP)
            self.button_b.switch_to_input(pull=digitalio.Pull.UP)
            self.display = st7789.ST7789(
                board.SPI(), cs=self.cs, dc=self.dc, rst=None, baudrate=64_000_000,
                width=135, height=240, x_offset=53, y_offset=40,
            )
            self.width, self.height, self.rotation = self.display.height, self.display.width, 90
            self.font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13
            )
            self.font_title = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17
            )
            self.font_step = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
            )
            self.font_timer = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38
            )
            self.font_enjoy = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
            )
            self.available = True
            threading.Thread(target=self._loop, args=(assistant,), daemon=True).start()
            print("MiniPiTFT enabled: Button A=START (GPIO23), Button B=END (GPIO24)")
        except Exception as exc:
            print(f"MiniPiTFT disabled ({exc}). Stop piscreen.service and check Lab 2 packages.")

    def _draw(self, state: dict[str, Any]) -> None:
        image = self.Image.new("RGB", (self.width, self.height), "#071018")
        draw = self.ImageDraw.Draw(image)
        mode = str(state.get("mode", "")).upper()
        mode_color = {
            "LISTENING": "#45d483", "THINKING": "#ffc857",
            "SPEAKING": "#66a6ff", "TIMER": "#45d483",
        }.get(mode, "#b7c5d8")
        hide_status = mode in {"IDLE", "STOPPED", "PASTA_DONE", "STEAK_DONE"}
        finished = mode in {"PASTA_DONE", "STEAK_DONE"}
        if not hide_status:
            draw.text((5, 3), mode[:12], font=self.font_small, fill=mode_color)

        if finished:
            draw.text(
                (self.width // 2, 29), str(state.get("title", "")),
                anchor="mm", font=self.font_title, fill="white",
            )
            draw.text(
                (self.width // 2, self.height // 2 + 12),
                "Enjoy your meal!", anchor="mm",
                font=self.font_enjoy, fill="#7ef0ad",
            )
            self.display.image(image, self.rotation)
            return

        if mode == "IDLE":
            draw.text(
                (self.width // 2, self.height // 2 - 15),
                str(state.get("title", "")), anchor="mm",
                font=self.font_title, fill="white",
            )
            draw.text(
                (self.width // 2, self.height // 2 + 16),
                str(state.get("body", "")), anchor="mm",
                font=self.font_small, fill="#d6deea",
            )
            self.display.image(image, self.rotation)
            return

        title_y = 5 if hide_status else 20
        draw.text(
            (5, title_y), str(state.get("title", ""))[:25],
            font=self.font_title, fill="white",
        )
        subtitle = str(state.get("subtitle", ""))
        if subtitle:
            draw.text((5, title_y + 21), subtitle[:28], font=self.font_step, fill="#aebdd0")

        remaining = state.get("timer_remaining")
        if remaining is not None:
            clock = f"{remaining // 60:02d}:{remaining % 60:02d}"
            draw.text(
                (self.width // 2, self.height // 2 + 7), clock,
                anchor="mm", font=self.font_timer, fill="#7ef0ad",
            )
        elif state.get("title") == "Confirm the timer":
            draw.text(
                (self.width // 2, self.height // 2 + 7),
                str(state.get("body", "")), anchor="mm",
                font=self.font_timer, fill="#ffc857",
            )
        else:
            y = title_y + (43 if subtitle else 25)
            body_lines: list[str] = []
            for paragraph in str(state.get("body", "")).splitlines():
                body_lines.extend(textwrap.wrap(paragraph, width=34) or [""])
            for line in body_lines[:2]:
                draw.text((5, y), line, font=self.font_small, fill="#d6deea")
                y += 15

        commands = " / ".join(str(item) for item in state.get("commands", []))
        command_lines = textwrap.wrap(commands, width=34)[:2]
        y = self.height - 5 - 15 * len(command_lines)
        for line in command_lines:
            draw.text((5, y), line, font=self.font_small, fill="#8fc2ff")
            y += 15
        self.display.image(image, self.rotation)

    def _loop(self, assistant: "Assistant") -> None:
        last_a = False
        last_b = False
        while not assistant.stop_event.is_set():
            a_pressed = not self.button_a.value
            b_pressed = not self.button_b.value
            if a_pressed and not last_a:
                assistant.start_session()
            if b_pressed and not last_b:
                assistant.stop_session()
            last_a, last_b = a_pressed, b_pressed
            self._draw(assistant.snapshot())
            time.sleep(0.08)


class Assistant:
    def __init__(self, args: argparse.Namespace) -> None:
        self.lock = threading.RLock()
        self.speech_lock = threading.Lock()
        self.speech_token = 0
        self.speaking = threading.Event()
        self.stop_event = threading.Event()
        self.ready = False
        self.active = False
        self.current = "idle"
        self.previous: list[str] = []
        self.pending_seconds: int | None = None
        self.pending_duration_text = ""
        self.pending_timer_kind: str | None = None
        self.add_time_return: str | None = None
        self.last_instruction = ""
        self.timer_end: float | None = None
        self.timer_target: str | None = None
        self.idle_return_deadline: float | None = None
        self.demo_timers = args.demo_timers
        self.model_name = args.model
        self.vad_path = args.vad_model
        self.voice_path = args.voice
        self.min_silence = args.min_silence
        self.recognizer: WhisperModel | None = None
        self.voice: PiperVoice | None = None
        self.state: dict[str, Any] = {
            "mode": "loading", "title": "Cooking Assistant",
            "body": "Loading speech models…", "commands": ["Please wait"],
            "transcript": "", "history": [],
        }
        self.hardware = MiniPiTFT(self)

    def initialise(self) -> None:
        if not self.vad_path.is_file():
            raise FileNotFoundError(f"VAD model not found: {self.vad_path}")
        if not self.voice_path.is_file():
            raise FileNotFoundError(f"Piper voice not found: {self.voice_path}")
        print("Loading Whisper and Piper models...", flush=True)
        self.recognizer = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        self.voice = PiperVoice.load(str(self.voice_path))
        self.ready = True
        self._show_scene("idle")
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._timer_loop, daemon=True).start()
        print("Ready. Press the physical START button.", flush=True)

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            result = dict(self.state)
            result["timer_remaining"] = (
                max(0, int(round(self.timer_end - time.monotonic())))
                if self.timer_end is not None else None
            )
            return result

    def _show_scene(self, key: str) -> None:
        scene = SCENES[key]
        self.current = key
        if key not in {"pasta_done", "steak_done"}:
            self.idle_return_deadline = None
        with self.lock:
            self.state.update(
                mode="listening" if self.active else key,
                title=scene["title"], subtitle=scene.get("subtitle", ""),
                body=scene["body"], commands=list(scene["commands"]),
            )

    def transition(self, key: str, remember_previous: bool = True) -> None:
        if remember_previous and self.current in SCENES and self.current not in {"idle", "stopped"}:
            self.previous.append(self.current)
            self.previous = self.previous[-20:]
        if key in {"pasta_done", "steak_done"}:
            self.active = False
        self._show_scene(key)
        self.speak(str(SCENES[key].get("say", "")))

    def start_session(self) -> None:
        if not self.ready:
            return
        sd.stop()
        self.cancel_timer()
        self.active = True
        self.previous.clear()
        self.pending_seconds = None
        self.pending_duration_text = ""
        self.pending_timer_kind = None
        self.idle_return_deadline = None
        self.transition("ask_recipe", remember_previous=False)

    def stop_session(self) -> None:
        if not self.ready:
            return
        sd.stop()
        self.cancel_timer()
        self.active = False
        self.previous.clear()
        self.idle_return_deadline = None
        self._show_scene("stopped")
        self.speak(str(SCENES["stopped"]["say"]))

    def go_back(self) -> None:
        if self.previous:
            self.transition(self.previous.pop(), remember_previous=False)
        else:
            self.speak("There is no previous step.", remember=False)

    def repeat(self) -> None:
        if self.last_instruction:
            self.speak(self.last_instruction, remember=False)

    def speak(self, text: str, remember: bool = True) -> None:
        if not text:
            return
        if remember:
            self.last_instruction = text
        with self.lock:
            self.speech_token += 1
            token = self.speech_token
            self.speaking.set()
        threading.Thread(target=self._speak_worker, args=(text, token), daemon=True).start()

    def _speak_worker(self, text: str, token: int) -> None:
        if self.voice is None:
            self.speaking.clear()
            return
        with self.speech_lock:
            self.speaking.set()
            with self.lock:
                self.state["mode"] = "speaking"
                self.state["history"].append({"role": "device", "text": text})
                self.state["history"] = self.state["history"][-20:]
            try:
                for chunk in self.voice.synthesize(text):
                    if token != self.speech_token:
                        break
                    audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
                    sd.play(audio, samplerate=chunk.sample_rate)
                    sd.wait()
            finally:
                if token == self.speech_token:
                    self.speaking.clear()
                    with self.lock:
                        if self.current in {"pasta_done", "steak_done", "stopped"}:
                            self.idle_return_deadline = time.monotonic() + 5
                        if self.timer_end is not None:
                            self.state["mode"] = "timer"
                        elif self.active:
                            self.state["mode"] = "listening"
                        else:
                            self.state["mode"] = self.current

    def _confirm_duration(self, seconds: int, duration_text: str, timer_kind: str) -> None:
        self.pending_seconds = seconds
        self.pending_duration_text = duration_text
        self.pending_timer_kind = timer_kind
        self.previous.append(self.current)
        self.current = "confirm_duration"
        with self.lock:
            self.state.update(
                title="Confirm the timer", subtitle="",
                body=format_duration(seconds),
                commands=["Yes", "No", "Repeat", "Stop"],
            )
        self.speak(f"You said {duration_text}. Is that correct?")

    def _start_cooking_timer(self) -> None:
        assert self.pending_seconds is not None and self.pending_timer_kind is not None
        seconds, kind = self.pending_seconds, self.pending_timer_kind
        duration_text = self.pending_duration_text
        if kind == "pasta":
            target, label = "pasta_finish", "Pasta timer"
            body = "Heat the tomato sauce with garlic and olive oil."
            message = (
                f"Okay. I have started a {duration_text} timer. Meanwhile, heat the tomato sauce "
                "with garlic and olive oil in a separate pan."
            )
        elif kind == "steak_first":
            target, label, body = "steak_flip", "Steak first side", "First-side timer running"
            message = f"Okay. I have started a {duration_text} timer."
        elif kind == "steak_second":
            target, label, body = "steak_temperature", "Steak second side", "Second-side timer running"
            message = f"Okay. I have started another {duration_text} timer."
        else:
            target = self.add_time_return or "ask_recipe"
            label, body = "Extra cooking time", "Extra-time timer running"
            message = f"Okay. I have added {duration_text}."
        self._start_timer(seconds, target, label, body)
        self.speak(message)

    def _start_timer(self, seconds: int, target: str, label: str, body: str) -> None:
        timer_seconds = 10 if self.demo_timers else seconds
        with self.lock:
            self.timer_end = time.monotonic() + timer_seconds
            self.timer_target = target
            self.current = "timer"
            self.state.update(
                mode="timer", title=label, subtitle="", body=body,
                commands=["Add time", "Repeat", "Stop"],
            )

    def cancel_timer(self) -> None:
        with self.lock:
            self.timer_end = None
            self.timer_target = None

    def _ask_add_time(self, preserve_return: bool = False) -> None:
        if not preserve_return:
            self.add_time_return = self.current
        self.current = "add_time"
        with self.lock:
            self.state.update(
                title="Add cooking time", subtitle="", body="How much additional time?",
                commands=["Say minutes or seconds", "Go back", "Stop"],
            )
        self.speak("How much additional time would you like to add?")

    def handle_transcript(self, heard: str) -> None:
        text = heard.lower().strip()
        with self.lock:
            self.idle_return_deadline = None
            self.state["transcript"] = heard
            self.state["history"].append({"role": "user", "text": heard})
            self.state["history"] = self.state["history"][-20:]
        if any(word in text for word in ("stop", "end recipe", "quit")):
            self.stop_session(); return
        if "repeat" in text:
            self.repeat(); return
        if "go back" in text or text == "back":
            self.go_back(); return
        if not self.active:
            return

        key = self.current
        if key == "ask_recipe":
            recipe = detect_recipe(text)
            if recipe == "pasta":
                self.transition("pasta_ingredients"); return
            if recipe == "steak":
                self.transition("steak_ingredients"); return
        elif key in {"pasta_ingredients", "steak_ingredients"} and "start" in text:
            self.transition("pasta_step_1" if key.startswith("pasta") else "steak_step_1"); return
        elif key == "pasta_step_1" and "next" in text:
            self.transition("pasta_step_2"); return
        elif key == "pasta_step_2":
            duration = extract_duration(text)
            if duration:
                self._confirm_duration(*duration, "pasta"); return
        elif key == "pasta_finish":
            if "next" in text:
                self.transition("pasta_done"); return
            if "add" in text and "time" in text:
                self._ask_add_time(); return
        elif key == "pasta_done" and ("choose" in text or "recipe" in text):
            self.transition("ask_recipe"); return
        elif key == "steak_step_1" and "next" in text:
            self.transition("steak_step_2"); return
        elif key == "steak_step_2" and "next" in text:
            self.transition("steak_step_3"); return
        elif key == "steak_step_3":
            duration = extract_duration(text)
            if duration:
                self._confirm_duration(*duration, "steak_first"); return
        elif key == "steak_flip" and "next" in text:
            self.transition("steak_second_side"); return
        elif key == "steak_second_side":
            duration = extract_duration(text)
            if duration:
                self._confirm_duration(*duration, "steak_second"); return
        elif key == "steak_temperature":
            if "start" in text and "rest" in text:
                self._start_timer(180, "steak_done", "Rest the steak", "Rest for at least 3 minutes.")
                self.speak("Okay. Let the steak rest for at least three minutes. I have started the resting timer.")
                return
            if "add" in text and "time" in text:
                self._ask_add_time(); return
        elif key == "steak_done" and ("choose" in text or "recipe" in text):
            self.transition("ask_recipe"); return
        elif key == "confirm_duration":
            if any(word in text for word in ("yes", "yeah", "correct", "right")):
                self._start_cooking_timer(); return
            if any(word in text for word in ("no", "wrong", "incorrect")):
                if self.pending_timer_kind == "add_time":
                    if self.previous and self.previous[-1] == "add_time":
                        self.previous.pop()
                    self._ask_add_time(preserve_return=True)
                    return
                previous = self.previous.pop() if self.previous else "ask_recipe"
                self.transition(previous, remember_previous=False); return
        elif key == "add_time":
            duration = extract_duration(text)
            if duration:
                self._confirm_duration(*duration, "add_time"); return
        self.speak("Sorry, I didn't understand. Please try again.", remember=False)

    def _timer_loop(self) -> None:
        while not self.stop_event.wait(0.2):
            target: str | None = None
            return_to_idle = False
            with self.lock:
                if self.timer_end is not None and time.monotonic() >= self.timer_end:
                    self.timer_end = None
                    target = self.timer_target
                    self.timer_target = None
                if (
                    self.idle_return_deadline is not None
                    and time.monotonic() >= self.idle_return_deadline
                ):
                    self.idle_return_deadline = None
                    return_to_idle = True
            if target:
                self.transition(target)
            if return_to_idle:
                self.active = False
                self.previous.clear()
                with self.lock:
                    self.state["transcript"] = ""
                self._show_scene("idle")

    def _listen_loop(self) -> None:
        assert self.recognizer is not None
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(self.vad_path)
        config.silero_vad.min_silence_duration = self.min_silence
        config.silero_vad.min_speech_duration = 0.25
        config.sample_rate = SAMPLE_RATE
        vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        window = config.silero_vad.window_size
        buffer = np.empty(0, dtype=np.float32)
        samples_per_read = int(0.1 * SAMPLE_RATE)
        print(f"Listening with {self.min_silence:.1f}s endpointing...", flush=True)
        with sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
            while not self.stop_event.is_set():
                chunk, _ = stream.read(samples_per_read)
                mono = chunk.reshape(-1)
                if not self.active or self.speaking.is_set():
                    buffer = np.empty(0, dtype=np.float32)
                    continue
                buffer = np.concatenate([buffer, mono])
                while len(buffer) > window:
                    vad.accept_waveform(buffer[:window]); buffer = buffer[window:]
                while not vad.empty():
                    utterance = np.array(vad.front.samples, dtype=np.float32)
                    vad.pop()
                    with self.lock:
                        self.state["mode"] = "thinking"
                    segments, _ = self.recognizer.transcribe(
                        utterance,
                        beam_size=3,
                        initial_prompt=(
                            "The recipe choices are steak and pasta. Other commands are start "
                            "cooking, next, repeat, go back, stop, yes, and no. The user may say "
                            "a duration in minutes or seconds."
                        ),
                        condition_on_previous_text=False,
                    )
                    heard = " ".join(segment.text.strip() for segment in segments).strip()
                    print(f"Recognized: {heard!r}", flush=True)
                    if heard:
                        self.handle_transcript(heard)
                    elif self.active:
                        self.speak("Sorry, I didn't hear anything. Please try again.", remember=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="base.en")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=0.7)
    parser.add_argument("--demo-timers", action="store_true", help="Use 10-second timers for filming")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    assistant = Assistant(args)
    assistant.initialise()
    while not assistant.stop_event.wait(1):
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")