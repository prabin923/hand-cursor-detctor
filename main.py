"""
Hand Gesture Cursor Control
============================
Control your computer's cursor using hand gestures detected via webcam.

Gestures:
  - Index finger up        -> Move cursor
  - Index + Middle pinch   -> Left click
  - Thumb + Index pinch    -> Right click
  - Two fingers up (V)     -> Scroll mode
  - Three fingers up       -> Window switch (swipe left/right)
  - Open palm              -> Idle (pause control)

Controls:
  - Press 'q' to quit
  - Press 'l' to toggle landmark drawing
  - Press 'm' to toggle mirror mode
"""

import json
import sys
from http.server import BaseHTTPRequestHandler


# Vercel detects `handler` only as a top-level class named handler (not `handler = ...`).
class handler(BaseHTTPRequestHandler):
    """
    Vercel Python HTTP entry (BaseHTTPRequestHandler subclass).
    Webcam cursor control runs on your machine; this URL only documents that.
    """

    def log_message(self, format, *args):
        return

    def do_GET(self):
        body = {
            "name": "Hand Gesture Cursor Control",
            "message": (
                "Gesture-driven cursor control uses your local webcam and OS; "
                "run it on your computer, not via this HTTP endpoint."
            ),
            "local_run": "pip install -r requirements.txt && python main.py",
        }
        payload = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run_desktop_app():
    """OpenCV + MediaPipe desktop loop (imports deferred so Vercel can load main.py)."""
    import time

    import cv2

    from hand_detector import HandDetector, Gesture
    from cursor_controller import CursorController
    from config import CONFIG

    GESTURE_COLORS = {
        Gesture.NONE: (128, 128, 128),
        Gesture.MOVE: (0, 255, 0),
        Gesture.LEFT_CLICK: (0, 165, 255),
        Gesture.RIGHT_CLICK: (0, 0, 255),
        Gesture.SCROLL: (255, 255, 0),
        Gesture.SWITCH_WINDOW: (255, 0, 255),
        Gesture.IDLE: (255, 200, 100),
    }

    GESTURE_LABELS = {
        Gesture.NONE: "No Gesture",
        Gesture.MOVE: "MOVE CURSOR",
        Gesture.LEFT_CLICK: "LEFT CLICK",
        Gesture.RIGHT_CLICK: "RIGHT CLICK",
        Gesture.SCROLL: "SCROLL MODE",
        Gesture.SWITCH_WINDOW: "SWITCH WINDOW",
        Gesture.IDLE: "IDLE (Open Palm)",
    }

    def draw_status_bar(frame, gesture, fps, frame_h, frame_w):
        bar_h = 50
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, frame_h - bar_h), (frame_w, frame_h), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        color = GESTURE_COLORS.get(gesture, (255, 255, 255))
        label = GESTURE_LABELS.get(gesture, "Unknown")

        cv2.circle(frame, (25, frame_h - 25), 10, color, -1)

        cv2.putText(frame, label, (45, frame_h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if CONFIG["show_fps"]:
            cv2.putText(frame, f"FPS: {int(fps)}", (frame_w - 120, frame_h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    def draw_active_zone(frame, frame_w, frame_h, margin):
        mx = int(frame_w * margin)
        my = int(frame_h * margin)
        cv2.rectangle(frame, (mx, my), (frame_w - mx, frame_h - my), (80, 80, 80), 1)

    print("Starting Hand Cursor Control...")
    print("Gestures:")
    print("  Index finger up       -> Move cursor")
    print("  Index + Middle pinch  -> Left click")
    print("  Thumb + Index pinch   -> Right click")
    print("  Two fingers (V sign)  -> Scroll mode")
    print("  Three fingers up      -> Switch window (swipe L/R)")
    print("  Open palm             -> Idle")
    print()
    print("Press 'q' to quit | 'l' toggle landmarks | 'm' toggle mirror")
    print()

    detector = HandDetector(
        max_hands=CONFIG["max_hands"],
        detection_confidence=CONFIG["detection_confidence"],
        tracking_confidence=CONFIG["tracking_confidence"],
    )
    controller = CursorController(CONFIG)

    cap = cv2.VideoCapture(CONFIG["camera_index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG["camera_width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["camera_height"])

    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check your camera connection.")
        sys.exit(1)

    show_landmarks = CONFIG["show_landmarks"]
    mirror = True
    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read from webcam.")
                break

            if mirror:
                frame = cv2.flip(frame, 1)

            frame_h, frame_w, _ = frame.shape

            hand_landmarks, handedness = detector.detect(frame)

            gesture = Gesture.NONE

            if hand_landmarks:
                positions = detector.get_landmark_positions(hand_landmarks, frame_w, frame_h)
                gesture, data = detector.classify_gesture(positions, CONFIG["pinch_threshold"])

                if gesture == Gesture.MOVE:
                    pos = data["position"]
                    controller.move_cursor(pos[0], pos[1], frame_w, frame_h)
                    controller.reset_scroll()
                    cv2.circle(frame, pos, 12, (0, 255, 0), 2)

                elif gesture == Gesture.LEFT_CLICK:
                    pos = data["position"]
                    clicked = controller.left_click(pos[0], pos[1], frame_w, frame_h)
                    controller.reset_scroll()
                    color = (0, 0, 255) if clicked else (0, 165, 255)
                    cv2.circle(frame, pos, 15, color, -1)

                elif gesture == Gesture.RIGHT_CLICK:
                    pos = data["position"]
                    clicked = controller.right_click(pos[0], pos[1], frame_w, frame_h)
                    controller.reset_scroll()
                    color = (255, 0, 0) if clicked else (128, 0, 128)
                    cv2.circle(frame, pos, 15, color, -1)

                elif gesture == Gesture.SCROLL:
                    pos = data["position"]
                    scroll_amount = controller.scroll(pos[1], frame_h)
                    controller.reset_switch()
                    mid = data["middle_position"]
                    cv2.line(frame, pos, mid, (255, 255, 0), 3)
                    direction = "UP" if scroll_amount > 0 else "DOWN" if scroll_amount < 0 else ""
                    if direction:
                        cv2.putText(frame, f"Scroll {direction}", (pos[0] + 20, pos[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                elif gesture == Gesture.SWITCH_WINDOW:
                    pos = data["position"]
                    mid = data["middle_position"]
                    controller.reset_scroll()
                    result = controller.switch_window(pos[0])
                    cv2.line(frame, pos, mid, (255, 0, 255), 3)
                    cv2.circle(frame, pos, 10, (255, 0, 255), -1)
                    if result == "next":
                        cv2.putText(frame, ">> NEXT WINDOW", (pos[0] + 20, pos[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                    elif result == "prev":
                        cv2.putText(frame, "<< PREV WINDOW", (pos[0] + 20, pos[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                    else:
                        cv2.putText(frame, "Swipe L/R", (pos[0] + 20, pos[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 150, 255), 2)

                elif gesture == Gesture.IDLE:
                    controller.reset_scroll()
                    controller.reset_switch()

                else:
                    controller.reset_scroll()
                    controller.reset_switch()

                if show_landmarks:
                    detector.draw_landmarks(frame, hand_landmarks, frame_w, frame_h)
            else:
                controller.reset_scroll()
                controller.reset_switch()

            draw_active_zone(frame, frame_w, frame_h, CONFIG["frame_margin"])

            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time

            draw_status_bar(frame, gesture, fps, frame_h, frame_w)

            cv2.imshow(CONFIG["window_name"], frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('l'):
                show_landmarks = not show_landmarks
            elif key == ord('m'):
                mirror = not mirror

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Hand Cursor Control stopped.")


def main():
    run_desktop_app()


if __name__ == "__main__":
    main()
