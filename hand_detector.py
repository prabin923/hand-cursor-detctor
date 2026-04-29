"""
Hand detection and gesture recognition using MediaPipe Tasks API.
Detects 21 hand landmarks and classifies gestures for cursor control.
"""

import mediapipe as mp
import cv2
import math
import os
from enum import Enum


class Gesture(Enum):
    NONE = "none"
    MOVE = "move"            # Index finger pointing up
    LEFT_CLICK = "left_click"   # Index + middle finger pinch
    RIGHT_CLICK = "right_click" # Thumb + index pinch
    SCROLL = "scroll"        # Two fingers up (V)
    SWITCH_WINDOW = "switch_window"  # Three fingers up (index+middle+ring)
    IDLE = "idle"            # Open palm


class HandDetector:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.7):
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")

        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

        # For drawing
        self.draw_utils = mp.tasks.vision.drawing_utils
        self.draw_styles = mp.tasks.vision.drawing_styles
        self.hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

        # Landmark indices
        self.WRIST = 0
        self.THUMB_TIP = 4
        self.INDEX_TIP = 8
        self.INDEX_MCP = 5
        self.MIDDLE_TIP = 12
        self.MIDDLE_MCP = 9
        self.RING_TIP = 16
        self.RING_MCP = 13
        self.PINKY_TIP = 20
        self.PINKY_MCP = 17

        self._frame_timestamp = 0

    def detect(self, frame):
        """Detect hands in a BGR frame. Returns (landmarks_list, handedness) or (None, None)."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._frame_timestamp += 33  # ~30fps in ms
        results = self.landmarker.detect_for_video(mp_image, self._frame_timestamp)

        if results.hand_landmarks:
            return results.hand_landmarks[0], results.handedness[0] if results.handedness else None
        return None, None

    def get_landmark_positions(self, hand_landmarks, frame_w, frame_h):
        """Convert normalized landmarks to pixel coordinates. Returns dict of {id: (x, y)}."""
        positions = {}
        for idx, lm in enumerate(hand_landmarks):
            positions[idx] = (int(lm.x * frame_w), int(lm.y * frame_h))
        return positions

    def _distance(self, p1, p2):
        """Euclidean distance between two (x, y) points."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _is_finger_up(self, positions, tip_id, mcp_id):
        """Check if a finger is extended (tip is above MCP joint)."""
        return positions[tip_id][1] < positions[mcp_id][1]

    def _is_thumb_out(self, positions):
        """Check if thumb is extended outward."""
        return abs(positions[self.THUMB_TIP][0] - positions[self.WRIST][0]) > \
               abs(positions[self.INDEX_MCP][0] - positions[self.WRIST][0]) * 0.5

    def classify_gesture(self, positions, pinch_threshold=40):
        """
        Classify the current hand gesture based on landmark positions.

        Returns (Gesture, extra_data) where extra_data depends on gesture type.
        """
        index_up = self._is_finger_up(positions, self.INDEX_TIP, self.INDEX_MCP)
        middle_up = self._is_finger_up(positions, self.MIDDLE_TIP, self.MIDDLE_MCP)
        ring_up = self._is_finger_up(positions, self.RING_TIP, self.RING_MCP)
        pinky_up = self._is_finger_up(positions, self.PINKY_TIP, self.PINKY_MCP)
        thumb_out = self._is_thumb_out(positions)

        fingers_up = sum([index_up, middle_up, ring_up, pinky_up])

        # Thumb + Index pinch = Right click
        thumb_index_dist = self._distance(positions[self.THUMB_TIP], positions[self.INDEX_TIP])
        if thumb_index_dist < pinch_threshold and not middle_up:
            return Gesture.RIGHT_CLICK, {"position": positions[self.INDEX_TIP]}

        # Index + Middle pinch = Left click
        index_middle_dist = self._distance(positions[self.INDEX_TIP], positions[self.MIDDLE_TIP])
        if index_up and middle_up and index_middle_dist < pinch_threshold and not ring_up:
            return Gesture.LEFT_CLICK, {"position": positions[self.INDEX_TIP]}

        # Three fingers up (index + middle + ring, spread) = Window switch mode
        if index_up and middle_up and ring_up and not pinky_up and index_middle_dist >= pinch_threshold:
            return Gesture.SWITCH_WINDOW, {
                "position": positions[self.INDEX_TIP],
                "middle_position": positions[self.MIDDLE_TIP],
            }

        # Two fingers up (index + middle, spread) = Scroll mode
        if index_up and middle_up and not ring_up and not pinky_up and index_middle_dist >= pinch_threshold:
            return Gesture.SCROLL, {
                "position": positions[self.INDEX_TIP],
                "middle_position": positions[self.MIDDLE_TIP],
            }

        # Only index finger up = Move cursor
        if index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.MOVE, {"position": positions[self.INDEX_TIP]}

        # All fingers up = Idle / open palm
        if fingers_up >= 4:
            return Gesture.IDLE, {}

        # Fist or unrecognized
        return Gesture.NONE, {}

    def draw_landmarks(self, frame, hand_landmarks, frame_w, frame_h):
        """Draw hand landmarks and connections on the frame."""
        # Draw connections
        for connection in self.hand_connections:
            start_lm = hand_landmarks[connection.start]
            end_lm = hand_landmarks[connection.end]
            start_pt = (int(start_lm.x * frame_w), int(start_lm.y * frame_h))
            end_pt = (int(end_lm.x * frame_w), int(end_lm.y * frame_h))
            cv2.line(frame, start_pt, end_pt, (0, 255, 0), 2)

        # Draw landmark points
        for lm in hand_landmarks:
            pt = (int(lm.x * frame_w), int(lm.y * frame_h))
            cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    def close(self):
        """Release the landmarker resources."""
        self.landmarker.close()
