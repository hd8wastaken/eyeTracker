import cv2
import numpy as np
import math
import time

win_w, win_h = 900, 500
er = 110
cx, cy = 450, 260
max_travel = er - int(er * 0.4) - 10

print("pupil should sweep in a circle. press q to close.")

t0 = time.time()
while True:
    canvas = np.full((win_h, win_w, 3), (255, 255, 255), dtype=np.uint8)

    t = time.time() - t0
    ang = t * 1.5
    trav = max_travel * 0.8
    px = cx + math.cos(ang) * trav
    py = cy + math.sin(ang) * trav

    cv2.circle(canvas, (cx, cy), er, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(canvas, (cx, cy), er, (40, 40, 40), 3, cv2.LINE_AA)
    cv2.circle(canvas, (int(px), int(py)), int(er * 0.4), (10, 10, 10), -1, cv2.LINE_AA)

    dist_from_center = math.hypot(px - cx, py - cy)
    assert dist_from_center <= max_travel + 1, "pupil escaped its eye radius"

    cv2.imshow("moving eye test", canvas)
    if cv2.waitKey(16) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
print("PASS: pupil moved and stayed within bounds")