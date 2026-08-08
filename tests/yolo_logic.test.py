import sys
import os
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

print("testing yolo classes (no camera, no model)...")

sys.path.insert(0, os.path.join(_ROOT, "src", "yolo"))

import types
ult = types.ModuleType("ultralytics")
class _FakeYOLO:
    def __init__(self, *a, **k): pass
    def fuse(self): pass
    def __call__(self, *a, **k): return [type("R", (), {"boxes": None})()]
ult.YOLO = _FakeYOLO
sys.modules["ultralytics"] = ult

import importlib.util
spec = importlib.util.spec_from_file_location("yolo_logic", os.path.join(_ROOT, "src", "yolo", "logic.py"))
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

trk = mod.tracker()
dt = trk.update(100, 100)
assert dt > 0, "dt must be positive"
time.sleep(0.05)
dt2 = trk.update(120, 110)
assert dt2 > 0
assert abs(trk.vel_x) > 0, "vel_x should be non-zero after movement"
print("  tracker: PASS")

import math
er  = 110
pr  = int(er * 0.42)
mt  = er - pr - 6 - 10
e   = mod.eye(300, 260, er)
e.smooth(300 + mt, 260)
dist = math.hypot(e.px - e.cx, e.py - e.cy)
assert dist <= mt + 1, f"pupil too far: {dist:.1f}"
print("  eye smooth: PASS")

import numpy as np
frame  = np.zeros((480, 640, 3), dtype=np.uint8)
boxes  = mod._detect(mod._YOLO("x"), frame)
assert isinstance(boxes, list), "boxes should be a list"
print("  _detect stub: PASS")

print("PASS: all yolo logic unit tests passed.")
