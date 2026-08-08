import cv2
import numpy as np
import time
import os
import sys
import math
import traceback
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
from addons.loader import AddonManager, ctx

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class _fake:
        def __getattr__(self, n): return ""
    Fore = _fake(); Style = _fake()

try:
    from ultralytics import YOLO as _YOLO
except ImportError:
    print("ultralytics not installed. run: pip install ultralytics")
    sys.exit(1)


def logr(msg, c=""):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{c}[{ts}] {msg}{Style.RESET_ALL}")


def pick_cam():
    logr("scanning cams...", Fore.CYAN)
    found = []
    for i in range(5):
        try:
            bk = cv2.CAP_DSHOW if os.name == "nt" else 0
            cap = cv2.VideoCapture(i, bk)
            if cap.isOpened():
                ok, _ = cap.read()
                if ok:
                    found.append(i)
                cap.release()
        except Exception:
            pass

    if not found:
        logr("no cams found, using 0", Fore.YELLOW)
        return 0
    if len(found) == 1:
        logr(f"using cam {found[0]}", Fore.GREEN)
        return found[0]

    print(f"{Fore.CYAN}cams: {found}{Style.RESET_ALL}")
    while True:
        c = input("pick cam index: ").strip()
        if c.isdigit() and int(c) in found:
            return int(c)


class eye:
    def __init__(self, cx, cy, r):
        self.cx = cx
        self.cy = cy
        self.r  = r
        self.px = float(cx)
        self.py = float(cy)
        self._vx = 0.0
        self._vy = 0.0

    def smooth(self, tx, ty):
        self._vx = self._vx * 0.6 + (tx - self.px) * 0.4
        self._vy = self._vy * 0.6 + (ty - self.py) * 0.4
        self.px += self._vx * 0.55
        self.py += self._vy * 0.55

    def draw(self, canvas):
        cx, cy, r = int(self.cx), int(self.cy), self.r
        px, py    = int(self.px), int(self.py)
        pr        = int(r * 0.42)

        # shadow ring + sclera
        cv2.circle(canvas, (cx, cy), r + 2, (200, 200, 200), -1, cv2.LINE_AA)
        cv2.circle(canvas, (cx, cy), r,     (250, 250, 250), -1, cv2.LINE_AA)

        # limbal ring
        cv2.circle(canvas, (cx, cy), r, (30, 30, 30), 3, cv2.LINE_AA)

        # blue (BGR: high B, medium G, low R)
        cv2.circle(canvas, (px, py), pr + 5, (200, 130, 50), -1, cv2.LINE_AA)

        # pupil
        cv2.circle(canvas, (px, py), pr, (8, 8, 12), -1, cv2.LINE_AA)

        # primary highlight
        hx = int(px - pr * 0.38)
        hy = int(py - pr * 0.38)
        cv2.circle(canvas, (hx, hy), max(3, pr // 3), (255, 255, 255), -1, cv2.LINE_AA)

        # secondary highlight
        h2x = int(px + pr * 0.30)
        h2y = int(py + pr * 0.28)
        cv2.circle(canvas, (h2x, h2y), max(1, pr // 6), (220, 230, 255), -1, cv2.LINE_AA)


class tracker:
    def __init__(self):
        self.last_cx = None
        self.last_cy = None
        self.vel_x   = 0.0
        self.vel_y   = 0.0
        self.last_t  = time.time()

    def update(self, cx, cy):
        now = time.time()
        dt  = max(1e-3, now - self.last_t)
        self.last_t = now
        if self.last_cx is not None:
            self.vel_x = self.vel_x * 0.65 + (cx - self.last_cx) / dt * 0.35
            self.vel_y = self.vel_y * 0.65 + (cy - self.last_cy) / dt * 0.35
        self.last_cx = cx
        self.last_cy = cy
        return dt


def _detect(model, frame):
    results = model(frame, verbose=False, conf=0.45, imgsz=320)[0]
    boxes = []
    if results.boxes is not None:
        for b in results.boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = map(int, b[:4])
            boxes.append((x1, y1, x2 - x1, y2 - y1))
    return boxes


def main():
    logr("starting robot eyes [yolo]", Fore.CYAN)

    logr("loading yolo face model...", Fore.YELLOW)
    try:
        model = _YOLO(os.path.join(_HERE, "model.pt"))
        model.fuse()
    except Exception as e:
        logr(f"fatal: {e}", Fore.RED)
        sys.exit(1)
    logr("model ready", Fore.GREEN)

    ci = pick_cam()
    bk = cv2.CAP_DSHOW if os.name == "nt" else 0
    cap = cv2.VideoCapture(ci, bk)
    if not cap.isOpened():
        logr(f"fatal: cant open cam {ci}", Fore.RED)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)

    win_w, win_h = 900, 500
    er = 110
    left  = eye(300, 260, er)
    right = eye(600, 260, er)
    max_travel = er - int(er * 0.42) - 6 - 10

    WIN = "robot eyes"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, win_w, win_h)

    trk       = tracker()
    show_prev = True
    fails     = 0

    # run yolo every other frame, cache boxes in between for fps
    _cached_faces = []
    _detect_frame = 0
    DETECT_EVERY  = 2

    addons = AddonManager(
        folder=os.path.join(_ROOT, "addons"),
        log=lambda m, c=Fore.MAGENTA: logr(m, c)
    )
    addons.dispatch("on_start", ctx(log=logr, win_w=win_w, win_h=win_h, eyes=(left, right)))

    logr("running. q/esc quit, f toggle preview", Fore.CYAN)

    _frame_t = time.perf_counter()

    while True:
        try:
            ok, frame = cap.read()
            if not ok or frame is None:
                fails += 1
                logr(f"grab fail ({fails})", Fore.YELLOW)
                if fails > 20:
                    logr("reconnecting cam", Fore.YELLOW)
                    cap.release()
                    time.sleep(0.5)
                    cap = cv2.VideoCapture(ci, bk)
                    fails = 0
                continue
            fails = 0

            frame = cv2.flip(frame, 1)
            fh, fw = frame.shape[:2]

            # only run yolo every DETECT_EVERY frames
            if _detect_frame % DETECT_EVERY == 0:
                _cached_faces = _detect(model, frame)
            _detect_frame += 1
            faces = _cached_faces

            canvas = np.full((win_h, win_w, 3), (255, 255, 255), dtype=np.uint8)

            logr(f"{'-'*60}", Fore.MAGENTA)
            logr(f"faces={len(faces)}", Fore.CYAN)

            actx = ctx(log=logr, frame=frame, gray=None, canvas=canvas,
                       faces=len(faces), boxes=faces,
                       win_w=win_w, win_h=win_h, eyes=(left, right), key=-1)
            addons.dispatch("on_frame", actx)

            if faces:
                total_a = sum(f[2] * f[3] for f in faces)
                wcx = sum((f[0] + f[2] / 2.0) * (f[2] * f[3]) for f in faces) / total_a
                wcy = sum((f[1] + f[3] / 2.0) * (f[2] * f[3]) for f in faces) / total_a

                for (fx, fy, fw2, fh2) in faces:
                    cv2.rectangle(frame, (fx, fy), (fx + fw2, fy + fh2), (0, 210, 90), 2)

                logr(f"weighted center=({wcx:.1f},{wcy:.1f}) over {len(faces)} face(s)", Fore.WHITE)

                dt = trk.update(wcx, wcy)
                logr(f"dt={dt*1000:.1f}ms vel=({trk.vel_x:.1f},{trk.vel_y:.1f})px/s", Fore.YELLOW)

                lead_t = 0.04
                pred_x = wcx + trk.vel_x * lead_t
                pred_y = wcy + trk.vel_y * lead_t
                logr(f"predicted pos ({lead_t*1000:.0f}ms ahead)=({pred_x:.1f},{pred_y:.1f})", Fore.YELLOW)

                dx  = pred_x - fw / 2.0
                dy  = pred_y - fh / 2.0
                hd  = math.hypot(fw / 2.0, fh / 2.0)
                dist = math.hypot(dx, dy)
                dn  = min(1.0, dist / hd)
                ang = math.atan2(dy, dx)

                logr(f"dx={dx:.1f} dy={dy:.1f} dist={dist:.1f} dn={dn:.3f} ang={ang:.3f}rad", Fore.GREEN)

                curve_dn = math.sin(dn * math.pi / 2)
                trav     = curve_dn * max_travel

                rot = math.pi
                ox  =  math.cos(rot + ang) * trav
                oy  = -math.sin(rot + ang) * trav

                logr(f"curve_dn={curve_dn:.3f} trav={trav:.2f} offset=({ox:.2f},{oy:.2f})", Fore.GREEN)

                for e in (left, right):
                    opx, opy = e.px, e.py
                    tx = e.cx + ox
                    ty = e.cy + oy
                    e.smooth(tx, ty)
                    logr(f"  eye@({e.cx},{e.cy}) {opx:.1f},{opy:.1f} -> {e.px:.1f},{e.py:.1f}", Fore.BLUE)

                addons.dispatch("on_face_found", actx)
            else:
                logr("no face, holding last pupil position", Fore.RED)
                addons.dispatch("on_face_lost", actx)

            left.draw(canvas)
            right.draw(canvas)

            if show_prev:
                ph  = int(win_h * 0.22)
                pw  = int(ph * fw / fh)
                sm  = cv2.resize(frame, (pw, ph))
                canvas[10:10 + ph, 10:10 + pw] = sm
                cv2.rectangle(canvas, (10, 10), (10 + pw, 10 + ph), (0, 0, 0), 1)

            addons.dispatch("on_draw", actx)

            cv2.imshow(WIN, canvas)

            now   = time.perf_counter()
            spent = (now - _frame_t) * 1000
            wait  = max(1, int(16 - spent))
            _frame_t = now

            k = cv2.waitKey(wait) & 0xFF
            if k in (ord("q"), 27):
                break
            elif k == ord("f"):
                show_prev = not show_prev
            elif k != 255:
                actx.key = k
                addons.dispatch("on_key", actx)

        except Exception as e:
            logr(f"frame err: {e}", Fore.RED)
            traceback.print_exc()
            time.sleep(0.05)

    logr("shutting down", Fore.CYAN)
    addons.dispatch("on_stop", ctx(log=logr))
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logr("interrupted", Fore.CYAN)
    except Exception as e:
        logr(f"fatal :(, error: {e}", Fore.RED)
        traceback.print_exc()
        sys.exit(1)
