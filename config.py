"""
Configuration for the hand cursor control app.
Adjust these values to tune sensitivity and behavior.
"""

CONFIG = {
    # Hand detection
    "max_hands": 1,
    "detection_confidence": 0.7,
    "tracking_confidence": 0.7,

    # Gesture thresholds
    "pinch_threshold": 40,  # pixels — distance below which a pinch is detected

    # Cursor control
    "smoothing": 5,           # higher = smoother but slower response (1-10)
    "click_cooldown": 0.5,    # seconds between clicks
    "scroll_speed": 10,       # scroll sensitivity multiplier
    "frame_margin": 0.1,      # ignore outer 10% of frame for comfort

    # Camera
    "camera_index": 0,        # webcam device index
    "camera_width": 640,
    "camera_height": 480,

    # Display
    "show_landmarks": True,
    "show_fps": True,
    "show_gesture": True,
    "window_name": "Hand Cursor Control",
}
