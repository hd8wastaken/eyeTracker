import cv2
import numpy as np

win_w, win_h = 900, 500
canvas = np.full((win_h, win_w, 3), (255, 255, 255), dtype=np.uint8)

er = 110
left_c = (300, 260)
right_c = (600, 260)

for c in (left_c, right_c):
    cv2.circle(canvas, c, er, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(canvas, c, er, (40, 40, 40), 3, cv2.LINE_AA)
    cv2.circle(canvas, c, int(er * 0.4), (10, 10, 10), -1, cv2.LINE_AA)

cv2.namedWindow("render test", cv2.WINDOW_NORMAL)
cv2.resizeWindow("render test", win_w, win_h)
print("window should be visible now. press q to close.")

while True:
    cv2.imshow("render test", canvas)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
print("PASS: window opened and closed without error.")