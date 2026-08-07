<div align="center">

# eyeTrack™

<img src="https://img.shields.io/badge/python-3.9+-3572A5?style=flat-square&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/opencv-5.0-5C3EE8?style=flat-square&logo=opencv&logoColor=white"/>
<img src="https://img.shields.io/badge/platform-windows%20%7C%20mac%20%7C%20linux-222?style=flat-square"/>
<img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white"/>

**a python webcam face tracker using cascade frontalface**

</div>

---

## requirements

- python 3.9+
- webcam 720p or better

```sh
pip install -r requirements.txt
```

to run, open one of the run files:

| platform | command |
|---|---|
| windows | `run.bat` |
| mac / linux | `./run.sh` |

---

## Basic controls:

| key | action |
|---|---|
| `q` / `esc` | quit |
| `f` | toggle webcam preview inset |

> if no cascade file is found locally, the app will attempt to download one automatically. (If internet connection is unstable the app will use the fallback.)

---

## addons

drop a `.py` file into `addons/` and it is loaded automatically at startup no registration needed.

define any combination of these hooks (all optional, all receive a single `ctx` object):

| hook | fires |
|---|---|
| `on_start(c)` | once, before the loop |
| `on_frame(c)` | every frame, after detection |
| `on_face_found(c)` | frames where ≥1 face was detected |
| `on_face_lost(c)` | frames where no face was detected |
| `on_draw(c)` | after eyes are drawn, before display |
| `on_key(c)` | a key other than `q` / `esc` / `f` was pressed |
| `on_stop(c)` | once, on shutdown |

**context fields:** `log`, `frame`, `gray (grayscale frame)`, `canvas`, `faces`, `boxes`, `win_w`, `win_h`, `eyes`, `key`


### example addons:

| addon | what it does |
|---|---|
| ~~`siren.py`~~ | ~~plays a siren after your face is gone 1.5 s, repeats every 2.5 s, stops when you return~~ removed. |
| `overlay.py` | draws fps, face count and away-timer on the canvas press `o` to toggle |

**Example:**

```python
# addons/example.py
NAME = "example"
ENABLED = True

def on_face_lost(c):
    c.log("son come back")

def on_face_found(c):
    c.log("hi bro ur back")
```


## docker

```sh
# build
build.bat          # windows
./build.sh         # linux / mac

# run
docker run --rm -it tracker
```

> on docker cannot access the host webcam without a virtual camera bridge.
