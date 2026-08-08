<div align="center">

# itrack

<img src="https://img.shields.io/badge/Python-3.9+-FFD43B?style=for-the-badge&logo=python&logoColor=blue"/>
<img src="https://img.shields.io/badge/YOLOv8-ultralytics-00ADEF?style=for-the-badge"/>
<img src="https://img.shields.io/badge/OpenCV-5.0-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"/>
<img src="https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white"/>
<img src="https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white"/>
<img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black"/>

<br/>

**a python webcam eye tracker**
uses yolov8n-face

</div>

---

## requirements

- python **3.9+**
- webcam **720p** or better

```sh
pip install -r src/yolo/requirements.txt
```

on first run `yolov8n-face.pt` is downloaded automatically (~6 MB) by ultralytics.

to run:

| platform | command |
|---|---|
| windows | `run.bat` |
| mac / linux | `./run.sh` |

---

## controls

| key | action |
|---|---|
| `q` / `esc` | quit |
| `f` | toggle webcam preview inset |
| `o` | toggle stats overlay (overlay addon) |

---

## Haar Cascade (frontalface) version

| feature | cascade | yolo |
|---|---|---|
| detector | haar cascade (2001) | yolov8n-face neural net |
| angles / occlusion | struggles | handles well |
| false positives | common | rare |
| first run | instant | downloads ~6 MB model |
| gpu acceleration | no | yes (if torch+cuda installed) |
| iris color | dark | blue |
| no-face behavior | holds position | holds position |
| detection cadence | every frame | every 2 frames (cached) |

---

## addons

the yolo version uses the same addon system as the cascade version. drop a `.py` file into `addons/`
at the project root and it loads automatically.

full addon documentation: [DOCS.md](../../DOCS.md)

### example addons

| addon | what it does |
|---|---|
| `overlay.py` | draws fps, face count and away-timer on the canvas - press `o` to toggle |


---

## tests

```sh
python tests/yolo_eyes_render.test.py   # visual: blue iris sweeps in a circle
python tests/yolo_logic.test.py         # headless: tracker, eye, _detect unit tests
```

---

## tips

- **slow fps** - yolo runs inference at `imgsz=320` by default (fast). raise to 640 in `_detect()` for better detection at the cost of speed.
- **gpu** - if you have an nvidia gpu, `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121` will make yolo significantly faster.
- **confidence** - the `conf=0.45` threshold in `_detect()` controls how strict detection is. lower it to catch more faces; raise it to reduce false positives.
