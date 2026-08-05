import cv2
import numpy as np
import time
import os
import sys
import math
import urllib.request
import traceback
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class fake:
        def __getattr__(self, n):
            return ""
    Fore = fake()
    Style = fake()


def logr(msg, c=""):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{c}[{ts}] {msg}{Style.RESET_ALL}")


def get_cascade():
    fn = "haarcascade_frontalface_default.xml"
    p = os.path.join(cv2.data.haarcascades, fn)

    if not os.path.isfile(p):
        d = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            url = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/" + fn
            logr(f"downloading cascade from {url}", Fore.YELLOW)
            urllib.request.urlretrieve(url, p)

    c = cv2.CascadeClassifier(p)
    if c.empty():
        raise RuntimeError("cascade load failed")
    return c


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
        self.r = r
        self.px = cx
        self.py = cy

    def draw(self, canvas):
        cv2.circle(canvas, (int(self.cx), int(self.cy)), self.r, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(canvas, (int(self.cx), int(self.cy)), self.r, (40, 40, 40), 3, cv2.LINE_AA)
        pr = int(self.r * 0.4)
        cv2.circle(canvas, (int(self.px), int(self.py)), pr, (10, 10, 10), -1, cv2.LINE_AA)
        hx = int(self.px - pr * 0.35)
        hy = int(self.py - pr * 0.35)
        cv2.circle(canvas, (hx, hy), max(2, pr // 4), (255, 255, 255), -1, cv2.LINE_AA)


class tracker:
    def __init__(self):
        self.last_cx = None
        self.last_cy = None
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.last_t = time.time()

    def update(self, cx, cy):
        now = time.time()
        dt = max(1e-3, now - self.last_t)
        self.last_t = now

        if self.last_cx is not None:
            new_vel_x = (cx - self.last_cx) / dt
            new_vel_y = (cy - self.last_cy) / dt
            self.vel_x = self.vel_x * 0.7 + new_vel_x * 0.3
            self.vel_y = self.vel_y * 0.7 + new_vel_y * 0.3

        self.last_cx = cx
        self.last_cy = cy
        return dt


def main():
    logr("starting robot eyes", Fore.CYAN)

    try:
        cascade = get_cascade()
    except Exception as e:
        logr(f"fatal: {e}", Fore.RED)
        sys.exit(1)

    ci = pick_cam()
    bk = cv2.CAP_DSHOW if os.name == "nt" else 0
    cap = cv2.VideoCapture(ci, bk)
    if not cap.isOpened():
        logr(f"fatal: cant open cam {ci}", Fore.RED)
        sys.exit(1)

    win_w, win_h = 900, 500
    er = 110
    left = eye(300, 260, er)
    right = eye(600, 260, er)
    max_travel = er - int(er * 0.4) - 10

    trk = tracker()
    show_prev = True
    fails = 0

    cv2.namedWindow("robot eyes", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("robot eyes", win_w, win_h)

    logr("running. q/esc quit, f toggle preview", Fore.CYAN)

    while True:
        try:
            ok, frame = cap.read()
            if not ok or frame is None:
                fails += 1
                logr(f"grab fail ({fails})", Fore.YELLOW)
                if fails > 20:
                    logr("reconnecting cam", Fore.YELLOW)
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(ci, bk)
                    fails = 0
                time.sleep(0.05)
                continue
            fails = 0

            frame = cv2.flip(frame, 1)
            fh, fw = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(25, 25))

            canvas = np.full((win_h, win_w, 3), (255, 255, 255), dtype=np.uint8)

            logr(f"{'-'*60}", Fore.MAGENTA)
            logr(f"faces={len(faces)}", Fore.CYAN)

            if len(faces) > 0:
                total_w = sum(f[2] * f[3] for f in faces)
                wcx = sum((f[0] + f[2] / 2.0) * (f[2] * f[3]) for f in faces) / total_w
                wcy = sum((f[1] + f[3] / 2.0) * (f[2] * f[3]) for f in faces) / total_w

                for (fx, fy, fwid, fhei) in faces:
                    cv2.rectangle(frame, (fx, fy), (fx + fwid, fy + fhei), (0, 255, 0), 2)

                logr(f"weighted center=({wcx:.1f},{wcy:.1f}) over {len(faces)} face(s)", Fore.WHITE)

                dt = trk.update(wcx, wcy)
                logr(f"dt={dt*1000:.1f}ms vel=({trk.vel_x:.1f},{trk.vel_y:.1f})px/s", Fore.YELLOW)

                lead_t = 0.05
                pred_x = wcx + trk.vel_x * lead_t
                pred_y = wcy + trk.vel_y * lead_t
                logr(f"predicted pos ({lead_t*1000:.0f}ms ahead)=({pred_x:.1f},{pred_y:.1f})", Fore.YELLOW)

                dx = pred_x - (fw / 2.0)
                dy = pred_y - (fh / 2.0)
                hd = math.sqrt((fw / 2.0) ** 2 + (fh / 2.0) ** 2)
                dist = math.hypot(dx, dy)
                dn = min(1.0, dist / hd)
                ang = math.atan2(dy, dx)

                logr(f"dx={dx:.1f} dy={dy:.1f} dist={dist:.1f} dn={dn:.3f} ang={ang:.3f}rad", Fore.GREEN)

                curve_dn = math.sin(dn * math.pi / 2)
                trav = curve_dn * max_travel

                rot = math.pi
                rx = math.cos(rot) * math.cos(ang) - math.sin(rot) * math.sin(ang)
                ry = math.sin(rot) * math.cos(ang) + math.cos(rot) * math.sin(ang)
                ox = rx * trav
                oy = -ry * trav

                logr(f"curve_dn={curve_dn:.3f} trav={trav:.2f} offset=({ox:.2f},{oy:.2f})", Fore.GREEN)

                for e in (left, right):
                    opx, opy = e.px, e.py
                    tx = e.cx + ox
                    ty = e.cy + oy
                    e.px = e.px + (tx - e.px) * 0.35
                    e.py = e.py + (ty - e.py) * 0.35
                    logr(f"  eye@({e.cx},{e.cy}) {opx:.1f},{opy:.1f} -> {e.px:.1f},{e.py:.1f}", Fore.BLUE)
            else:
                logr("no face, holding last pupil position", Fore.RED)

            left.draw(canvas)
            right.draw(canvas)

            if show_prev:
                sm = cv2.resize(frame, (200, int(200 * fh / fw)))
                sh, sw = sm.shape[:2]
                canvas[10:10 + sh, 10:10 + sw] = sm
                cv2.rectangle(canvas, (10, 10), (10 + sw, 10 + sh), (0, 0, 0), 1)

            cv2.imshow("robot eyes", canvas)

            k = cv2.waitKey(1) & 0xFF
            if k == ord("q") or k == 27:
                break
            elif k == ord("f"):
                show_prev = not show_prev

            time.sleep(0.01)

        except Exception as e:
            logr(f"frame err: {e}", Fore.RED)
            traceback.print_exc()
            time.sleep(0.1)

    logr("shutting down", Fore.CYAN)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logr("interrupted", Fore.CYAN)
    except Exception as e:
        logr(f"FATAL: {e}", Fore.RED)
        traceback.print_exc()
        sys.exit(1)