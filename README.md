### iTrack™

a python webcam eye tracker. detects your face and moves an eye to follow you

## requirements

- python 3.9+
- camera over 720p
- requirements in `requirements.txt`

install deps:

```
pip install -r requirements.txt
```
(to run open one of the run files; run.bat < windows, run.sh < mac / linux)

## addons

drop a `.py` file in `addons/` and it gets loaded automatically at startup. define any of these
hooks — all optional, all take a single ctx object:

| hook | when |
|---|---|
| `on_start(c)` | once, before the loop |
| `on_frame(c)` | every frame, after detection |
| `on_face_found(c)` | frames where a face was detected |
| `on_face_lost(c)` | frames where no face was detected |
| `on_draw(c)` | after the eyes are drawn, before display |
| `on_key(c)` | a key was pressed (`c.key`), other than q/esc/f |
| `on_stop(c)` | once, on shutdown |

ctx fields: `log`, `frame`, `gray`, `canvas`, `faces` (count), `boxes`, `win_w`, `win_h`, `eyes`, `key`.

set `ENABLED = False` in an addon to skip it. an addon that raises is logged and the app keeps running.

shipped addons:

- `siren.py` — plays `src/assets/siren.wav` when your face has been gone 1.5s, repeats every 2.5s, stops when you return
- `overlay.py` — draws fps, face count and away-timer on the canvas. press `o` to toggle

## tests


;;todo dodac wiecej testow zeby nie musiec odpalac glownej logiki aby testowac dane funckje

```
python tests/cascade.test.py
python tests/eye.test.py
python tests/rendering.test.py
```

## docker

build the image:

windows:

```
build.bat
```
linux / mac:

```
./build.sh
```

windows, linux & mac
```
docker run --rm -it tracker
```

;;todo naprawic aby docker na linux poprawnie wykrywal kamerke


on windows/mac, docker cannot access the host webcam directly without extra setup (virutal cam bridge), best to run without the docker container.


- q / esc — quit
- f — toggle webcam preview inset
- o — toggle the stats overlay (overlay addon)
- if no cascade file is found locally, the app will attempt to download one