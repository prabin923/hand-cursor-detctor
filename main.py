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

Vercel loads this file only for a small WSGI `app`; the webcam loop lives in desktop.py.
"""

import json


def _vercel_wsgi(environ, start_response):
    body = json.dumps(
        {
            "name": "Hand Gesture Cursor Control",
            "message": (
                "Gesture-driven cursor control uses your local webcam and OS; "
                "run it on your computer, not via this HTTP endpoint."
            ),
            "local_run": "pip install -r requirements.txt && python main.py",
        },
        indent=2,
    ).encode("utf-8")
    start_response(
        "200 OK",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


app = _vercel_wsgi


def main():
    from desktop import run_desktop_app

    run_desktop_app()


if __name__ == "__main__":
    main()
