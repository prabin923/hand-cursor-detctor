# Hand Gesture Cursor Control

Control your computer's cursor using hand gestures detected via your webcam. Works on macOS, Windows, and Linux.

## How It Works

Uses MediaPipe to detect 21 hand landmarks in real-time from your webcam feed, classifies gestures, and maps them to cursor actions via PyAutoGUI.

## Gestures

| Gesture | Action |
|---------|--------|
| Index finger up | Move cursor |
| Index + Middle finger pinch | Left click |
| Thumb + Index finger pinch | Right click |
| Two fingers up (V sign) | Scroll mode (move hand up/down) |
| Open palm (all fingers) | Idle / pause |

## Setup

### 1. Install Python 3.8+

### 2. Install dependencies

```bash
cd hand-cursor-control
pip install -r requirements.txt
```

### 3. macOS permissions

On macOS, you need to grant:
- **Camera access** — System Settings > Privacy & Security > Camera
- **Accessibility access** — System Settings > Privacy & Security > Accessibility

Add your Terminal app (Terminal, iTerm2, etc.) to both lists.

### 4. Run

```bash
python main.py
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit |
| `l` | Toggle landmark drawing |
| `m` | Toggle mirror mode |

## Configuration

Edit `config.py` to adjust:

- **smoothing** (1-10): Higher = smoother cursor but slower response. Default: 5
- **click_cooldown**: Seconds between clicks to prevent accidental double-clicks. Default: 0.5
- **scroll_speed**: Scroll sensitivity. Default: 10
- **pinch_threshold**: Pixel distance for pinch detection. Default: 40
- **frame_margin**: Ignore outer edges of webcam frame. Default: 0.1 (10%)
- **detection_confidence**: MediaPipe detection threshold. Default: 0.7

## Troubleshooting

- **Cursor jumps around**: Increase `smoothing` in config.py
- **Clicks trigger too easily**: Decrease `pinch_threshold` or increase `click_cooldown`
- **Gestures not detected**: Ensure good lighting, keep hand within the active zone (gray rectangle)
- **Low FPS**: Reduce `camera_width`/`camera_height` in config.py
- **Permission denied (macOS)**: Add Terminal to Accessibility in System Settings

## Project Structure

```
hand-cursor-control/
  main.py              — Main app loop, webcam feed, UI overlay
  hand_detector.py     — MediaPipe hand detection + gesture classification
  cursor_controller.py — Screen mapping, smoothing, click/scroll actions
  config.py            — All tunable parameters
  requirements.txt     — Python dependencies
```
