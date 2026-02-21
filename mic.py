import queue
import sounddevice as sd
import json
import sys
import os
import time
import threading
import pyautogui
import subprocess
import psutil
from vosk import Model, KaldiRecognizer

# ==========================================================
# CONFIGURATION
# ==========================================================

MODEL_PATH = "vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
COOLDOWN_TIME = 0.8
WAKE_WORD_ENABLED = False
WAKE_WORD = "computer"

pyautogui.FAILSAFE = False

audio_queue = queue.Queue()
running = True
last_action_time = 0

# ==========================================================
# AUDIO CALLBACK
# ==========================================================

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

# ==========================================================
# LOGGING
# ==========================================================

def log_command(text, action):
    with open("voice_log.txt", "a") as f:
        f.write(f"{time.ctime()} | {text} -> {action}\n")

# ==========================================================
# INTENT DETECTION
# ==========================================================

def detect_intent(text):
    text = text.lower()

    # Navigation
    if any(w in text for w in ["next", "forward", "continue"]):
        return "NEXT"

    if any(w in text for w in ["previous", "go back", "back"]):
        return "PREVIOUS"

    # Enter / Select
    if any(w in text for w in ["enter", "select", "open it", "confirm"]):
        return "ENTER"

    # Scrolling
    if "scroll down" in text:
        return "SCROLL_DOWN"

    if "scroll up" in text:
        return "SCROLL_UP"

    # Mouse movement
    if "move mouse left" in text:
        return "MOUSE_LEFT"

    if "move mouse right" in text:
        return "MOUSE_RIGHT"

    if "move mouse up" in text:
        return "MOUSE_UP"

    if "move mouse down" in text:
        return "MOUSE_DOWN"

    if "click" in text:
        return "LEFT_CLICK"

    if "right click" in text:
        return "RIGHT_CLICK"

    # Media control
    if "play" in text:
        return "MEDIA_PLAY"

    if "pause" in text:
        return "MEDIA_PAUSE"

    if "volume up" in text:
        return "VOLUME_UP"

    if "volume down" in text:
        return "VOLUME_DOWN"

    if "mute" in text:
        return "MUTE"

    # System
    if "shutdown" in text:
        return "SHUTDOWN"

    if "restart" in text:
        return "RESTART"

    if "sleep" in text:
        return "SLEEP"

    # Apps
    if "open browser" in text:
        return "OPEN_BROWSER"

    if "open terminal" in text:
        return "OPEN_TERMINAL"

    if "open files" in text:
        return "OPEN_FILES"

    # Window control
    if "switch window" in text:
        return "SWITCH_WINDOW"

    if "close window" in text:
        return "CLOSE_WINDOW"

    # Custom macros
    if "presentation mode" in text:
        return "PRESENTATION_MODE"

    if "coding mode" in text:
        return "CODING_MODE"

    if "exit program" in text:
        return "EXIT"

    return None

# ==========================================================
# ACTION EXECUTION
# ==========================================================

def execute_action(action):
    global last_action_time, running

    now = time.time()
    if now - last_action_time < COOLDOWN_TIME:
        return

    print("Executing:", action)

    try:

        if action == "NEXT":
            pyautogui.press("right")

        elif action == "PREVIOUS":
            pyautogui.press("left")

        elif action == "ENTER":
            pyautogui.press("enter")

        elif action == "SCROLL_DOWN":
            pyautogui.scroll(-400)

        elif action == "SCROLL_UP":
            pyautogui.scroll(400)

        elif action == "MOUSE_LEFT":
            pyautogui.moveRel(-100, 0)

        elif action == "MOUSE_RIGHT":
            pyautogui.moveRel(100, 0)

        elif action == "MOUSE_UP":
            pyautogui.moveRel(0, -100)

        elif action == "MOUSE_DOWN":
            pyautogui.moveRel(0, 100)

        elif action == "LEFT_CLICK":
            pyautogui.click()

        elif action == "RIGHT_CLICK":
            pyautogui.rightClick()

        elif action == "MEDIA_PLAY":
            pyautogui.press("space")

        elif action == "MEDIA_PAUSE":
            pyautogui.press("space")

        elif action == "VOLUME_UP":
            subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "5%+"])

        elif action == "VOLUME_DOWN":
            subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "5%-"])

        elif action == "MUTE":
            subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "toggle"])

        elif action == "SHUTDOWN":
            subprocess.call(["shutdown", "now"])

        elif action == "RESTART":
            subprocess.call(["reboot"])

        elif action == "SLEEP":
            subprocess.call(["systemctl", "suspend"])

        elif action == "OPEN_BROWSER":
            subprocess.Popen(["xdg-open", "https://www.google.com"])

        elif action == "OPEN_TERMINAL":
            subprocess.Popen(["lxterminal"])

        elif action == "OPEN_FILES":
            subprocess.Popen(["pcmanfm"])

        elif action == "SWITCH_WINDOW":
            pyautogui.hotkey("alt", "tab")

        elif action == "CLOSE_WINDOW":
            pyautogui.hotkey("alt", "f4")

        elif action == "PRESENTATION_MODE":
            pyautogui.press("f5")

        elif action == "CODING_MODE":
            subprocess.Popen(["code"])

        elif action == "EXIT":
            running = False

    except Exception as e:
        print("Error executing action:", e)

    last_action_time = now

# ==========================================================
# VOICE THREAD
# ==========================================================

def voice_loop():
    global running

    if not os.path.exists(MODEL_PATH):
        print("Model not found.")
        sys.exit(1)

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    with sd.RawInputStream(samplerate=SAMPLE_RATE,
                           blocksize=BLOCK_SIZE,
                           dtype='int16',
                           channels=1,
                           callback=audio_callback):

        print("Voice control active...")

        while running:
            data = audio_queue.get()

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")

                if text:
                    print("Heard:", text)

                    if WAKE_WORD_ENABLED:
                        if WAKE_WORD not in text:
                            continue

                    action = detect_intent(text)

                    if action:
                        log_command(text, action)
                        execute_action(action)

# ==========================================================
# MAIN
# ==========================================================

def main():

    print("===================================")
    print(" ADVANCED VOICE CONTROL SYSTEM ")
    print("===================================")
    print("Speak naturally. Example commands:")
    print("- go to next slide")
    print("- scroll down")
    print("- move mouse left")
    print("- open browser")
    print("- shutdown")
    print("- presentation mode")
    print("===================================")

    thread = threading.Thread(target=voice_loop)
    thread.start()

    try:
        while running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Stopping...")

    print("Voice system terminated.")

if __name__ == "__main__":
    main()