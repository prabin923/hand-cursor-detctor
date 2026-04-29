"""
Cursor control engine — maps hand landmark positions to screen actions.
Handles smoothing, coordinate mapping, clicking, scrolling, and window switching.
"""

import pyautogui
import time
import platform

# Disable pyautogui fail-safe pause for smoother movement
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True  # Move mouse to corner to abort

IS_MAC = platform.system() == "Darwin"


class CursorController:
    def __init__(self, config):
        self.screen_w, self.screen_h = pyautogui.size()
        self.smoothing = config.get("smoothing", 5)
        self.click_cooldown = config.get("click_cooldown", 0.5)
        self.scroll_speed = config.get("scroll_speed", 10)
        self.frame_margin = config.get("frame_margin", 0.1)  # ignore outer 10% of frame
        self.switch_threshold = config.get("switch_threshold", 80)  # px swipe to trigger
        self.switch_cooldown = config.get("switch_cooldown", 0.8)  # seconds between switches

        # State
        self.prev_x = self.screen_w // 2
        self.prev_y = self.screen_h // 2
        self.last_click_time = 0
        self.last_scroll_y = None
        self.is_clicking = False

        # Window switch state
        self.switch_start_x = None
        self.last_switch_time = 0

    def map_to_screen(self, hand_x, hand_y, frame_w, frame_h):
        """
        Map hand position in the webcam frame to screen coordinates.
        Uses a reduced region of the frame (excluding margins) for comfort.
        """
        margin_x = int(frame_w * self.frame_margin)
        margin_y = int(frame_h * self.frame_margin)

        # Clamp to active region
        active_w = frame_w - 2 * margin_x
        active_h = frame_h - 2 * margin_y

        rel_x = (hand_x - margin_x) / active_w
        rel_y = (hand_y - margin_y) / active_h

        # Clamp to [0, 1]
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))

        # Mirror X axis (webcam is mirrored)
        rel_x = 1.0 - rel_x

        screen_x = int(rel_x * self.screen_w)
        screen_y = int(rel_y * self.screen_h)

        return screen_x, screen_y

    def smooth_move(self, target_x, target_y):
        """Apply exponential smoothing to cursor movement to reduce jitter."""
        s = self.smoothing
        smooth_x = int(self.prev_x + (target_x - self.prev_x) / s)
        smooth_y = int(self.prev_y + (target_y - self.prev_y) / s)

        self.prev_x = smooth_x
        self.prev_y = smooth_y

        return smooth_x, smooth_y

    def move_cursor(self, hand_x, hand_y, frame_w, frame_h):
        """Map hand position to screen and move cursor smoothly."""
        screen_x, screen_y = self.map_to_screen(hand_x, hand_y, frame_w, frame_h)
        smooth_x, smooth_y = self.smooth_move(screen_x, screen_y)
        pyautogui.moveTo(smooth_x, smooth_y, _pause=False)
        return smooth_x, smooth_y

    def left_click(self, hand_x, hand_y, frame_w, frame_h):
        """Perform a left click with cooldown to prevent rapid repeated clicks."""
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            self.move_cursor(hand_x, hand_y, frame_w, frame_h)
            pyautogui.click(_pause=False)
            self.last_click_time = now
            return True
        return False

    def right_click(self, hand_x, hand_y, frame_w, frame_h):
        """Perform a right click with cooldown."""
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            self.move_cursor(hand_x, hand_y, frame_w, frame_h)
            pyautogui.rightClick(_pause=False)
            self.last_click_time = now
            return True
        return False

    def scroll(self, hand_y, frame_h):
        """Scroll based on vertical hand movement. Up = scroll up, down = scroll down."""
        if self.last_scroll_y is None:
            self.last_scroll_y = hand_y
            return 0

        delta = self.last_scroll_y - hand_y  # positive = hand moved up
        self.last_scroll_y = hand_y

        if abs(delta) > 3:  # dead zone to avoid accidental scrolls
            scroll_amount = int(delta / frame_h * self.scroll_speed * 20)
            if scroll_amount != 0:
                pyautogui.scroll(scroll_amount, _pause=False)
            return scroll_amount
        return 0

    def reset_scroll(self):
        """Reset scroll tracking when leaving scroll mode."""
        self.last_scroll_y = None

    def switch_window(self, hand_x):
        """
        Track horizontal hand swipe to switch windows.
        Swipe right -> next window (Cmd+Tab / Alt+Tab)
        Swipe left  -> previous window (Cmd+Shift+Tab / Alt+Shift+Tab)
        Returns: 'next', 'prev', or None
        """
        now = time.time()

        if self.switch_start_x is None:
            self.switch_start_x = hand_x
            return None

        delta = hand_x - self.switch_start_x

        if abs(delta) > self.switch_threshold and (now - self.last_switch_time) > self.switch_cooldown:
            self.last_switch_time = now
            self.switch_start_x = hand_x  # Reset for continuous swiping

            if IS_MAC:
                modifier = "command"
            else:
                modifier = "alt"

            if delta > 0:
                # Swiped right -> next window
                pyautogui.hotkey(modifier, "tab", _pause=False)
                return "next"
            else:
                # Swiped left -> previous window
                pyautogui.hotkey(modifier, "shift", "tab", _pause=False)
                return "prev"

        return None

    def reset_switch(self):
        """Reset window switch tracking when leaving switch mode."""
        self.switch_start_x = None

