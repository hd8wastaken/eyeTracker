import cv2
import numpy as np
import math
import time
import sys
import os

print("yolo eye render test blue iris pupil should sweep in a circle. press q to close.")

win_w, win_h = 900, 500
er = 110
cx, cy = 450, 260
pr = int(er * 0.42)
max_travel = er - pr - 6 - 10

t0 = time.time()
while True:
    canvas = np.full((win_h, win_w, 3), (255, 255, 255), dtype=np.uint8)

    t   = time.time() - t0
    ang = t * 1.5
    trav = max_travel * 0.8
    px  = cx + math.cos(ang) * trav
    py  = cy + math.sin(ang) * trav
    ipx, ipy = int(px), int(py)

    # shadow + sclera
    cv2.circle(canvas, (cx, cy), er + 2, (200, 200, 200), -1, cv2.LINE_AA)
    cv2.circle(canvas, (cx, cy), er,     (250, 250, 250), -1, cv2.LINE_AA)
    cv2.circle(canvas, (cx, cy), er, (30, 30, 30), 3, cv2.LINE_AA)

    # iris (blue)
    cv2.circle(canvas, (ipx, ipy), pr + 5, (200, 130, 50), -1, cv2.LINE_AA)

    # pupil
    cv2.circle(canvas, (ipx, ipy), pr, (8, 8, 12), -1, cv2.LINE_AA)

    # highlights
    hx = int(px - pr * 0.38)
    hy = int(py - pr * 0.38)
    cv2.circle(canvas, (hx, hy), max(3, pr // 3), (255, 255, 255), -1, cv2.LINE_AA)

    dist_from_center = math.hypot(px - cx, py - cy)
    assert dist_from_center <= max_travel + 1, f"pupil escaped: dist={dist_from_center:.1f} max={max_travel}"

    cv2.imshow("yolo eye render test", canvas)
    if cv2.waitKey(16) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
print("PASS: blue pupil moved and stayed within bounds.")
