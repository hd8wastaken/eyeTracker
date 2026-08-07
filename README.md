<div align="center">

# iTrack™

<img src="https://img.shields.io/badge/Python-3.9+-FFD43B?style=for-the-badge&logo=python&logoColor=blue"/>
<img src="https://img.shields.io/badge/OpenCV-5.0-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"/>
<img src="https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
<img src="https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white"/>
<img src="https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white"/>
<img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black"/>

<br/>

**a python webcam face tracker.**

</div>

---

## requirements

- python **3.9+**
- webcam **720p** or better
- deps listed in `requirements.txt`

```sh
pip install -r requirements.txt
```

to run, open one of the run files:

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
| `o` | toggle stats overlay |

> if no cascade file is found locally, the app will download one automatically.

---

## addons

drop a `.py` file into `addons/` and it is picked up automatically at startup — no registration needed.

define any of these hooks (all optional, all receive a single `ctx` object):

| hook | fires |
|---|---|
| `on_start(c)` | once, before the loop |
| `on_frame(c)` | every frame, after detection |
| `on_face_found(c)` | frames where ≥1 face was detected |
| `on_face_lost(c)` | frames where no face was detected |
| `on_draw(c)` | after eyes are drawn, before display |
| `on_key(c)` | a key other than `q` / `esc` / `f` was pressed |
| `on_stop(c)` | once, on shutdown |

**ctx fields:** `log`, `frame`, `gray`, `canvas`, `faces`, `boxes`, `win_w`, `win_h`, `eyes`, `key`

set `ENABLED = False` at the top of an addon to disable it without deleting it.
an addon that raises is logged and the app keeps running.

Documentation: [DOCS.md](DOCS.md)

### example addons

| addon | what it does |
|---|---|
| ~~`siren.py`~~ | ~~plays a siren after your face is gone 1.5 s, repeats every 2.5 s, stops when you return~~ |
| `overlay.py` | draws fps, face count and away-timer on the canvas — press `o` to toggle |

### quick example

```python
# addons/hello.py
NAME = "hello"

def on_face_lost(c):
    c.log("where did you go?")

def on_face_found(c):
    c.log("there you are")
```

---

## tests

```sh
python tests/cascade_frontalface.test.py
python tests/eyes_render.test.py
python tests/window_render.test.py
```

---

## docker

```sh
# build
build.bat        # windows
./build.sh       # linux / mac

# run
docker run --rm -it tracker
```

> on windows/mac docker cannot access the host webcam without a virtual camera bridge.
> best to run natively on those platforms.

