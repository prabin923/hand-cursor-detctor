"""
Hand Gesture Cursor Control
============================
Control your computer's cursor using hand gestures detected via webcam.

Gestures:
  - Index finger up        -> Move cursor
  - Index + Middle pinch   -> Left click
  - Thumb + Index pinch    -> Right click
  - Two fingers up (V)     -> Scroll mode
  - Open palm              -> Idle (pause control)

Controls:
  - Press 'q' to quit
  - Press 'l' to toggle landmark drawing
  - Press 'm' to toggle mirror mode
"""

import cv2
import time
import sys

from hand_detector import HandDetector, Gesture
from cursor_controller import CursorController
from config import CONFIG


# Gesture display colors (BGR)
GESTURE_COLORS = {
    Gesture.NONE: (128, 128, 128),
    Gesture.MOVE: (0, 255, 0),
    Gesture.LEFT_CLICK: (0, 165, 255),
    Gesture.RIGHT_CLICK: (0, 0, 255),
    Gesture.SCROLL: (255, 255, 0),
    Gesture.IDLE: (255, 200, 100),
}

GESTURE_LABELS = {
    Gesture.NONE: "No Gesture",
    Gesture.MOVE: "MOVE CURSOR",
    Gesture.LEFT_CLICK: "LEFT CLICK",
    Gesture.RIGHT_CLICK: "RIGHT CLICK",
    Gesture.SCROLL: "SCROLL MODE",
    Gesture.IDLE: "IDLE (Open Palm)",
}


def draw_status_bar(frame, gesture, fps, frame_h, frame_w):
    """Draw a translucent status bar at the bottom of the frame."""
    bar_h = 50
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, frame_h - bar_h), (frame_w, frame_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    color = GESTURE_COLORS.get(gesture, (255, 255, 255))
    label = GESTURE_LABELS.get(gesture, "Unknown")

    # Gesture indicator circle
    cv2.circle(frame, (25, frame_h - 25), 10, color, -1)

    # Gesture text
    cv2.putText(frame, label, (45, frame_h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # FPS counter
    if CONFIG["show_fps"]:
        cv2.putText(frame, f"FPS: {int(fps)}", (frame_w - 120, frame_h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)


def draw_active_zone(frame, frame_w, frame_h, margin):
    """Draw the active tracking zone rectangle."""
    mx = int(frame_w * margin)
    my = int(frame_h * margin)
    cv2.rectangle(frame, (mx, my), (frame_w - mx, frame_h - my), (80, 80, 80), 1)


def main():
    print("Starting Hand Cursor Control...")
    print("Gestures:")
    print("  Index finger up       -> Move cursor")
    print("  Index + Middle pinch  -> Left click")
    print("  Thumb + Index pinch   -> Right click")
    print("  Two fingers (V sign)  -> Scroll mode")
    print("  Open palm             -> Idle")
    print()
    print("Press 'q' to quit | 'l' toggle landmarks | 'm' toggle mirror")
    print()

    # Initialize components
    detector = HandDetector(
        max_hands=CONFIG["max_hands"],
        detection_confidence=CONFIG["detection_confidence"],
        tracking_confidence=CONFIG["tracking_confidence"],
    )
    controller = CursorController(CONFIG)

    # Open webcam
    cap = cv2.VideoCapture(CONFIG["camera_index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG["camera_width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["camera_height"])

    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check your camera connection.")
        sys.exit(1)

    show_landmarks = CONFIG["show_landmarks"]
    mirror = True
    prev_time = time.time()
    prev_gesture = Gesture.NONE

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read from webcam.")
                break

            if mirror:
                frame = cv2.flip(frame, 1)

            frame_h, frame_w, _ = frame.shape

            # Detect hand
            hand_landmarks, handedness = detector.detect(frame)

            gesture = Gesture.NONE

            if hand_landmarks:
                positions = detector.get_landmark_positions(hand_landmarks, frame_w, frame_h)
                gesture, data = detector.classify_gesture(positions, CONFIG["pinch_threshold"])

                # Execute cursor action based on gesture
                if gesture == Gesture.MOVE:
                    pos = data["position"]
                    controller.move_cursor(pos[0], pos[1], frame_w, frame_h)
                    controller.reset_scroll()
                    # Draw tracking point
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
                    # Draw scroll indicator
                    mid = data["middle_position"]
                    cv2.line(frame, pos, mid, (255, 255, 0), 3)
                    direction = "UP" if scroll_amount > 0 else "DOWN" if scroll_amount < 0 else ""
                    if direction:
                        cv2.putText(frame, f"Scroll {direction}", (pos[0] + 20, pos[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                elif gesture == Gesture.IDLE:
                    controller.reset_scroll()

                else:
                    controller.reset_scroll()

                # Draw landmarks
                if show_landmarks:
                    detector.draw_landmarks(frame, hand_landmarks, frame_w, frame_h)
            else:
                controller.reset_scroll()

            # Draw UI elements
            draw_active_zone(frame, frame_w, frame_h, CONFIG["frame_margin"])

            # Calculate FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time

            draw_status_bar(frame, gesture, fps, frame_h, frame_w)

            # Show frame
            cv2.imshow(CONFIG["window_name"], frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('l'):
                show_landmarks = not show_landmarks
            elif key == ord('m'):
                mirror = not mirror

            prev_gesture = gesture

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Hand Cursor Control stopped.")


if __name__ == "__main__":
    main()
