import cv2
import os
import urllib.request

fn = "haarcascade_frontalface_default.xml"
p = os.path.join(cv2.data.haarcascades, fn)

if not os.path.isfile(p):
    local_dir = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(local_dir, fn)
    if not os.path.isfile(p):
        url = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/" + fn
        print(f"downloading cascade from {url}")
        urllib.request.urlretrieve(url, p)

cascade = cv2.CascadeClassifier(p)
assert not cascade.empty(), "FAIL: cascade did not load"
print("cascade loaded ok")

bk = cv2.CAP_DSHOW if os.name == "nt" else 0
cap = cv2.VideoCapture(0, bk)
assert cap.isOpened(), "FAIL: could not open camera 0"
print("camera opened ok")

print("looking for faces. press q to close.")

detected_at_least_once = False

while True:
    ok, frame = cap.read()
    if not ok:
        print("frame grab failed")
        continue

    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(25, 25))

    if len(faces) > 0:
        detected_at_least_once = True

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    print(f"faces detected: {len(faces)}", end="\r")

    cv2.imshow("face detect test", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

print()
if detected_at_least_once:
    print("PASS: at least one face was detected during this run")
else:
    print("WARN: no face was detected during this run, try again facing the camera")