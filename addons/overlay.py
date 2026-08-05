import time
import cv2

NAME = "overlay"
ENABLED = True

_frames = 0
_fps = 0.0
_t0 = None
_faces = 0
_lost_at = None
_visible = True
_show = True


def on_start(c):
    global _t0
    _t0 = time.time()
    c.log("overlay: press o to toggle")


def on_frame(c):
    global _frames, _fps, _t0, _faces
    _faces = c.faces
    _frames += 1
    now = time.time()
    if now - _t0 >= 0.5:
        _fps = _frames / (now - _t0)
        _frames = 0
        _t0 = now


def on_face_found(c):
    global _lost_at, _visible
    _lost_at = None
    _visible = True


def on_face_lost(c):
    global _lost_at, _visible
    if _lost_at is None:
        _lost_at = time.time()
    _visible = False


def on_key(c):
    global _show
    if c.key == ord("o"):
        _show = not _show


def on_draw(c):
    if not _show:
        return

    canvas = c.canvas
    h, w = canvas.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX

    if _visible:
        status = f"tracking {_faces} face(s)"
        col = (0, 150, 0)
    else:
        away = time.time() - _lost_at if _lost_at else 0.0
        status = f"no face  {away:.1f}s"
        col = (0, 0, 220)

    lines = [(f"{_fps:.1f} fps", (90, 90, 90)), (status, col)]

    y = h - 18
    for text, colour in reversed(lines):
        cv2.putText(canvas, text, (14, y), font, 0.55, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(canvas, text, (14, y), font, 0.55, colour, 1, cv2.LINE_AA)
        y -= 24

    if not _visible:
        cv2.rectangle(canvas, (2, 2), (w - 3, h - 3), (0, 0, 220), 3)
