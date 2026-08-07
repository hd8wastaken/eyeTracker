<div align="center">

# addon docs

everything you need to write, configure and debug addons for iTrack.

</div>

---

## table of contents

- [how addons work](#how-addons-work)
- [file structure](#file-structure)
- [hooks reference](#hooks-reference)
- [context object reference](#ctx-object-reference)
- [module-level fields](#module-level-fields)
- [writing your first addon](#writing-your-first-addon)
- [keeping state between frames](#keeping-state-between-frames)
- [drawing on the canvas](#drawing-on-the-canvas)
- [responding to keypresses](#responding-to-keypresses)
- [doing async / heavy work](#doing-async--heavy-work)
- [bundled addons as examples](#bundled-addons-as-examples)
- [debugging](#debugging)
- [common mistakes](#common-mistakes)

---

## how addons work

at startup `addons/loader.py` scans the `addons/` directory alphabetically. for every `.py` file it
finds (except `loader.py` and files starting with `_`) it:

1. loads the module with `importlib` no `sys.path` pollution,
2. checks `ENABLED` (skips if `False`),
3. checks whether the module defines at least one known hook (skips if not),
4. calls `on_start` if defined,
5. adds it to the active list.

from that point `logic.py` calls `addons.dispatch("hook_name", ctx)` at the right moments in the
main loop. each dispatch iterates the active list and calls the hook on every addon that defines it.

**errors are isolated.** if your addon throws, it gets a timestamped log entry and the app moves on.
it will not crash the tracker or skip other addons.

---

## file structure

```
addons/
├── loader.py        the engine, do not edit unless you know what you're doing
├── siren.py         bundled: face-lost alarm
├── overlay.py       bundled: fps / face count overlay
└── your_addon.py    drop yours here
```

your addon is just a plain `.py` file. no class needed, no base class to inherit from. 

---

## hooks reference

all hooks are **optional**. define only what you need. every hook receives one positional argument
the `ctx` (context) object (described in the next section).

---

### `on_start(c)`

fires **once**, before the main loop begins.

use it to:
- log that your addon loaded,
- validate config / file paths,
- initialize state that depends on `c.win_w` / `c.win_h`.

```python
def on_start(c):
    c.log("my addon ready")
```

> `c.frame`, `c.canvas`, `c.faces`, `c.boxes`, `c.key` are **not available** here the camera
> hasn't started yet. available: `log`, `win_w`, `win_h`, `eyes`.

---

### `on_frame(c)`

fires **every frame**, after detection runs and before any drawing.

use it to:
- compute per-frame stats (fps counter, motion delta, etc.),
- inspect `c.faces` and `c.boxes`,
- update internal state.

```python
_total = 0

def on_frame(c):
    global _total
    _total += 1
```

> called regardless of whether a face was found. check `c.faces > 0` yourself if you care.

---

### `on_face_found(c)`

fires every frame where **at least one face** was detected.

called **every such frame**, not only on the transition from no-face to face. if you need to detect
the moment the face comes back, track a `_was_visible` flag yourself.

```python
_was_visible = False

def on_face_found(c):
    global _was_visible
    if not _was_visible:
        c.log("face appeared")
    _was_visible = True
```

---

### `on_face_lost(c)`

fires every frame where **no face** was detected.

```python
import time
_lost_at = None

def on_face_lost(c):
    global _lost_at
    if _lost_at is None:
module-level        _lost_at = time.time()
        c.log("face just disappeared")
    else:
        c.log(f"still missing for {time.time() - _lost_at:.1f}s")

def on_face_found(c):
    global _lost_at
    _lost_at = None
```

---

### `on_draw(c)`

fires after the eyes and camera preview are drawn onto `c.canvas`, right before the frame is shown
with `cv2.imshow`.

use it to draw anything extra on the canvas text, shapes, borders, overlays.

**mutate `c.canvas` directly** it is the live output array.

```python
import cv2

def on_draw(c):
    cv2.putText(
        c.canvas, f"{c.faces} face(s)",
        (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        (0, 0, 0), 1, cv2.LINE_AA
    )
```

> do **not** replace `c.canvas` with a new array that has no effect. mutate in place.

---

### `on_key(c)`

fires when the user presses a key **other than** `q`, `esc`, or `f` (those are handled by the main
loop before dispatch reaches addons).

`c.key` holds the key code as an integer. compare with `ord("x")` for printable keys.

```python
_enabled = True

def on_key(c):
    global _enabled
    if c.key == ord("t"):
        _enabled = not _enabled
        c.log(f"my addon {'on' if _enabled else 'off'}")
```

> `c.key` is only meaningful inside `on_key`. in other hooks it is set to `-1`.

---

### `on_stop(c)`

fires **once**, when the user quits (before the camera and window are released).

use it to:
- write a summary to a log file,
- stop background threads,
- release resources.

```python
_frame_count = 0

def on_stop(c):
    c.log(f"session over processed {_frame_count} frames")
```

---

## ctx object reference

every hook receives a `ctx` object. it is a simple attribute bag access fields with dot notation.

| field | type | available in | description |
|---|---|---|---|
| `log` | `callable(msg, color="")` | all hooks | timestamped logger. `c.log("hello")` |
| `frame` | `np.ndarray` (BGR) | on_frame and later | camera frame, already mirrored, face boxes drawn |
| `gray` | `np.ndarray` (gray) | on_frame and later | same frame in grayscale |
| `canvas` | `np.ndarray` (BGR) | on_frame and later | **the output canvas** mutate in on_draw |
| `faces` | `int` | on_frame and later | number of faces detected this frame |
| `boxes` | list of `(x,y,w,h)` | on_frame and later | raw detection rectangles |
| `win_w` | `int` | all hooks | canvas width (900) |
| `win_h` | `int` | all hooks | canvas height (500) |
| `eyes` | `tuple[eye, eye]` | all hooks | left and right eye objects |
| `key` | `int` | on_key only | pressed key code; `-1` elsewhere |

### the `eye` object

each item in `c.eyes` has:

| attr | description |
|---|---|
| `cx`, `cy` | center of the eye (fixed) |
| `r` | radius of the eye |
| `px`, `py` | current pupil position (updated every frame) |

you can read these to position overlays relative to the eyes:

```python
def on_draw(c):
    for eye in c.eyes:
        cv2.circle(c.canvas, (int(eye.cx), int(eye.cy)), eye.r + 5, (255, 0, 0), 1)
```

### the `log` function

```python
c.log("some message")               # white text
c.log("warning", Fore.YELLOW)       # colored needs colorama imported
```

the timestamp format is `HH:MM:SS.mmm`. logs go to stdout.

---

## module-level fields

these are read by the loader before any hook is called:

| field | type | default | description |
|---|---|---|---|
| `NAME` | `str` | filename without `.py` | label shown in log lines |
| `ENABLED` | `bool` | `True` | set `False` to skip this addon at load time |

```python
NAME = "my tracker"
ENABLED = True      # change to False to temporarily disable
```

---

## writing your first addon

minimal working example counts frames and logs a summary on exit:

```python
# addons/frame_counter.py
NAME = "frame counter"

_count = 0

def on_frame(c):
    global _count
    _count += 1

def on_stop(c):
    c.log(f"total frames: {_count}")
```

drop it in `addons/`, run the tracker. you will see `addons: loaded frame counter [on_frame, on_stop]`
in the startup log and the summary when you quit.

---

## keeping state between frames

use **module-level variables**. the module is imported once at startup and lives for the entire session.

```python
# good
_count = 0

def on_frame(c):
    global _count
    _count += 1
```

do **not** use `on_start` to store state on `c` the ctx object is created fresh each frame, so
anything you attach to it is gone next frame.

---

## drawing on the canvas

`c.canvas` is a `numpy.ndarray` of shape `(win_h, win_w, 3)` filled with white `(255, 255, 255)`.
it is recreated every frame, so you start fresh each time.

all standard OpenCV drawing functions work directly on it:

```python
import cv2
import numpy as np

def on_draw(c):
    h, w = c.canvas.shape[:2]

    # filled rectangle
    cv2.rectangle(c.canvas, (0, h - 40), (w, h), (30, 30, 30), -1)

    # text with outline trick (readable on any background)
    text = f"{c.faces} face(s)"
    pos = (10, h - 12)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(c.canvas, text, pos, font, 0.6, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.putText(c.canvas, text, pos, font, 0.6, (0, 200, 100), 1, cv2.LINE_AA)
```

**draw in `on_draw`, not `on_frame`.** by `on_frame` the canvas hasn't been drawn yet
the eyes are added later. drawing in `on_frame` means the eyes paint over your work.

---

## responding to keypresses

register a letter in `on_key` and avoid `q`, `f`, `o` (already taken):

```python
_show = True

def on_key(c):
    global _show
    if c.key == ord("h"):
        _show = not _show
        c.log(f"heatmap {'on' if _show else 'off'}")

def on_draw(c):
    if not _show:
        return
    # draw your thing
```

---

## doing async

hooks run synchronously inside the render loop. a slow hook drops fps.

for anything that takes more than a millisecond file writes, audio, network use a daemon thread:

```python
import threading

def _save_frame(frame):
    import cv2, time
    cv2.imwrite(f"temp/face_{time.time():.3f}.jpg", frame)

def on_face_lost(c):
    if c.faces == 0:
        t = threading.Thread(target=_save_frame, args=(c.frame.copy(),), daemon=True)
        t.start()
```

note `c.frame.copy()` the array is reused by the camera, so you must copy before handing it off.

---

## bundled addons as examples

### `overlay.py` canvas drawing + toggle key

shows how to:
- measure fps over a rolling window (not from startup),
- draw text with a white outline for legibility,
- draw a colored border around the whole canvas,
- wire an `on_key` toggle to an `on_draw` guard.

---

## debugging

**check the startup log.** the loader prints one line per addon:

```
addons: loaded siren [on_start, on_face_found, on_face_lost, on_stop]
addons: loaded overlay [on_start, on_frame, on_face_found, on_face_lost, on_draw, on_key]
addons: 2 active
```

if your addon is missing:
- `no hooks` your function names don't match any hook name (check for typos)
- `disabled` `ENABLED = False` is set
- `failed to load <name>: ...` a syntax or import error; full traceback follows

**use `c.log` freely.** it timestamps everything and goes to stdout where you can scroll back.

**test hooks in isolation** the loader is importable on its own:

```python
from addons.loader import AddonManager, ctx
import numpy as np

m = AddonManager(log=print)
c = ctx(log=print, canvas=np.full((500,900,3),255,dtype='uint8'),
        faces=0, boxes=[], win_w=900, win_h=500, eyes=(), key=-1)
m.dispatch("on_face_lost", c)
```

---

## common mistakes

| mistake | fix |
|---|---|
| function named `on_Frame` or `On_frame` | hooks are case-sensitive use lowercase exactly |
| `c.canvas = new_array` | assign into the existing array: `c.canvas[:] = new_array` or draw with cv2 |
| `time.sleep()` inside a hook | run in a thread sleeping stalls the render loop |
| reading `c.key` in `on_frame` | `c.key` is only valid inside `on_key`; it is `-1` everywhere else |
| storing state on `c` in `on_start` | ctx is recreated every frame use module globals |
| `c.frame` in `on_start` | frame is not available yet in `on_start` |
