tracker

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
- if no cascade file is found locally, the app will attempt to download one