import cv2
import dlib
import time
import pyautogui
import numpy as np
from scipy.spatial import distance as dist
from imutils import face_utils
from imutils.video import VideoStream

# ==========================================
# CONFIGURATION
# ==========================================

EAR_THRESHOLD = 0.23
EAR_CONSEC_FRAMES = 3
DOUBLE_BLINK_MAX_TIME = 0.6
LONG_BLINK_TIME = 1.2
COOLDOWN_TIME = 0.8

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

pyautogui.FAILSAFE = False

# ==========================================
# EYE ASPECT RATIO FUNCTION
# ==========================================

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# ==========================================
# BLINK DETECTOR CLASS
# ==========================================

class BlinkController:

    def __init__(self):
        self.frame_counter = 0
        self.last_blink_time = 0
        self.blink_start_time = 0
        self.cooldown = False
        self.cooldown_start = 0
        self.pending_single = False
        self.status_text = "Waiting..."

    def trigger_action(self, action):
        self.status_text = action
        print("Action:", action)

        if action == "NEXT":
            pyautogui.press("right")

        elif action == "PREVIOUS":
            pyautogui.press("left")

        elif action == "SELECT":
            pyautogui.press("enter")

        elif action == "SCROLL_UP":
            pyautogui.scroll(200)

        elif action == "SCROLL_DOWN":
            pyautogui.scroll(-200)

        self.cooldown = True
        self.cooldown_start = time.time()

    def process(self, ear):

        current_time = time.time()

        # Cooldown block
        if self.cooldown:
            if current_time - self.cooldown_start > COOLDOWN_TIME:
                self.cooldown = False
            else:
                return

        # Eye closed
        if ear < EAR_THRESHOLD:

            if self.frame_counter == 0:
                self.blink_start_time = current_time

            self.frame_counter += 1

        # Eye opened
        else:

            if self.frame_counter >= EAR_CONSEC_FRAMES:

                blink_duration = current_time - self.blink_start_time

                # Long blink
                if blink_duration >= LONG_BLINK_TIME:
                    self.trigger_action("SELECT")
                    self.pending_single = False

                else:
                    # Double blink detection
                    if (current_time - self.last_blink_time) <= DOUBLE_BLINK_MAX_TIME:
                        self.trigger_action("PREVIOUS")
                        self.pending_single = False
                    else:
                        self.pending_single = True

                self.last_blink_time = current_time

            self.frame_counter = 0

        # Handle single blink delay
        if self.pending_single:
            if (current_time - self.last_blink_time) > DOUBLE_BLINK_MAX_TIME:
                self.trigger_action("NEXT")
                self.pending_single = False

# ==========================================
# FPS COUNTER
# ==========================================

class FPSCounter:

    def __init__(self):
        self.start_time = time.time()
        self.frames = 0

    def update(self):
        self.frames += 1

    def get_fps(self):
        elapsed = time.time() - self.start_time
        return self.frames / elapsed if elapsed > 0 else 0

# ==========================================
# MAIN PROGRAM
# ==========================================

def main():

    print("[INFO] Loading face detector...")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    print("[INFO] Starting camera...")
    vs = VideoStream(src=0).start()
    time.sleep(2.0)

    controller = BlinkController()
    fps = FPSCounter()

    print("[INFO] Eye control started. Press 'q' to exit.")

    while True:

        frame = vs.read()
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        rects = detector(gray, 0)

        for rect in rects:

            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]

            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)

            ear = (leftEAR + rightEAR) / 2.0

            controller.process(ear)

            # Draw eye contours
            cv2.drawContours(frame, [cv2.convexHull(leftEye)], -1, (0,255,0), 1)
            cv2.drawContours(frame, [cv2.convexHull(rightEye)], -1, (0,255,0), 1)

            cv2.putText(frame, f"EAR: {ear:.2f}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

        fps.update()

        cv2.putText(frame, f"FPS: {fps.get_fps():.2f}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

        cv2.putText(frame, f"Status: {controller.status_text}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

        cv2.imshow("Eye Blink Controller (No UDP)", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    vs.stop()

if __name__ == "__main__":
    main()