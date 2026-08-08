# addon docs

everything you need to write, configure and debug addons for the yolo version of iTrack.

the addon system is **identical** to the cascade version. for the full reference see [DOCS.md](DOCS.md).

---

## table of contents

- [what is different from the cascade version](#what-is-different-from-the-cascade-version)
- [hooks reference](#hooks-reference)
- [ctx object reference](#ctx-object-reference)
- [module-level fields](#module-level-fields)
- [writing your first addon](#writing-your-first-addon)
- [keeping state between frames](#keeping-state-between-frames)
- [drawing on the canvas](#drawing-on-the-canvas)
- [doing async / heavy work](#doing-async--heavy-work)
- [debugging](#debugging)
- [common mistakes](#common-mistakes)

---

## what is different from the cascade version

| thing | cascade | yolo |
|---|---|---|
| `c.gray` | grayscale frame | always `None` — yolo works on color |
| detection cadence | every frame | every 2nd frame; `c.boxes` may be from the previous frame |
| `c.boxes` format | `(x, y, w, h)` | same `(x, y, w, h)` — converted internally |
| eye draw style | dark pupil | blue iris + dark pupil |
| window | 900x500 fixed | 900x500 fixed |

everything else — hooks, ctx fields, `ENABLED`, `NAME`, `on_start` / `on_stop` — is identical.

---

## hooks reference

all hooks are optional. define only what you need.

| hook | fires |
|---|---|
| `on_start(c)` | once, before the loop |
| `on_frame(c)` | every frame, after detection |
| `on_face_found(c)` | frames where at least one face was detected |
| `on_face_lost(c)` | frames where no face was detected |
| `on_draw(c)` | after the eyes are drawn, before display |
| `on_key(c)` | a key other than `q` / `esc` / `f` was pressed |
| `on_stop(c)` | once, on shutdown |

`on_face_found` and `on_face_lost` fire on **every matching frame**, not only on transitions.
track a flag yourself if you only want to react to the moment of change.

---

## ctx object reference

| field | type | available in | description |
|---|---|---|---|
| `log` | `callable` | all hooks | timestamped logger |
| `frame` | `np.ndarray` BGR | on_frame and later | camera frame, mirrored, with face boxes drawn |
| `gray` | `None` | always | not used by yolo — always None |
| `canvas` | `np.ndarray` BGR | on_frame and later | 900x500 output canvas — mutate in on_draw |
| `faces` | `int` | on_frame and later | number of detected faces |
| `boxes` | list of `(x,y,w,h)` | on_frame and later | detection rectangles (may be 1 frame stale) |
| `win_w` | `int` | all hooks | 900 |
| `win_h` | `int` | all hooks | 500 |
| `eyes` | `tuple[eye, eye]` | all hooks | left and right eye objects |
| `key` | `int` | on_key only | pressed key code; -1 elsewhere |

### the eye object

| attr | description |
|---|---|
| `cx`, `cy` | fixed center of the eye |
| `r` | radius |
| `px`, `py` | current pupil position (smoothed each frame) |

---

## module-level fields

| field | default | description |
|---|---|---|
| `NAME` | filename | label in log lines |
| `ENABLED` | `True` | set `False` to skip at load time |

---

## writing your first addon

```python
# addons/hello.py
NAME = "hello"

def on_face_lost(c):
    c.log("where did you go?")

def on_face_found(c):
    c.log("there you are")
```

drop in `addons/` at the project root. the yolo version loads from the same folder as the cascade version.

---

## keeping state between frames

use module-level variables. the module is loaded once and lives for the whole session.

```python
_count = 0

def on_frame(c):
    global _count
    _count += 1

def on_stop(c):
    c.log(f"processed {_count} frames")
```

do not store state on `c` — the ctx object is recreated every frame.

---

## drawing on the canvas

mutate `c.canvas` in `on_draw`. it is a fresh `(500, 900, 3)` numpy array each frame.

```python
import cv2

def on_draw(c):
    cv2.putText(c.canvas, f"faces: {c.faces}", (14, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
```

draw in `on_draw`, not `on_frame` — the eyes are painted after `on_frame` and before `on_draw`.

---

## doing async / heavy work

hooks are synchronous. anything slow will drop fps. use daemon threads:

```python
import threading

def on_face_lost(c):
    threading.Thread(
        target=lambda f: ...,
        args=(c.frame.copy(),),
        daemon=True
    ).start()
```

always copy `c.frame` before passing it to a thread — the array is reused by the camera.

---

## debugging

startup log shows which addons loaded and which hooks they registered:

```
addons: loaded overlay [on_start, on_frame, on_face_found, on_face_lost, on_draw, on_key]
addons: 1 active
```

if your addon is missing: `no hooks` means a typo in a function name, `disabled` means `ENABLED = False`,
`failed to load` has a full traceback below it.

---

## common mistakes

| mistake | fix |
|---|---|
| reading `c.gray` | always None in yolo version — work from `c.frame` (BGR) |
| `c.canvas = new_array` | mutate in place with cv2 drawing calls |
| blocking in a hook | run heavy work in a daemon thread |
| `c.key` in `on_frame` | only valid in `on_key`, -1 everywhere else |
| expecting `on_face_lost` only once | fires every "no-face" frame. use a flag for edge detection |
