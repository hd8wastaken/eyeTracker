# addons/siren.py
import os
import time
import threading
import winsound
import random

NAME = "siren"
ENABLED = False


_last_face_time = time.time()
_siren_playing = False
_siren_thread = None
_sound_files = []



files = [
    "src/assets/cbtm.wav",
    "src/assets/bored.wav",
    "src/assets/play.wav",
]
cd = 0.1 


def on_start(c):
    global _sound_files
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    

    for f in files:
        wav_path = os.path.join(script_dir, f)
        if os.path.exists(wav_path):
            _sound_files.append(wav_path)
            c.log(f"found {f}")
        else:
            c.log(f"{f} not found at {wav_path}")
    
    if not _sound_files:
        c.log("no siren files found")
    else:
        c.log(f"loaded {len(_sound_files)} siren files (winsound doesn't support volume control)")


def on_frame(c):
    global _last_face_time
    
    if c.faces > 0:
        _last_face_time = time.time()


def on_face_lost(c):
    global _siren_playing, _siren_thread
    
    if not _sound_files:
        return
    
    elapsed = time.time() - _last_face_time
    
    if elapsed >= cd and not _siren_playing:
        _siren_playing = True
        _siren_thread = threading.Thread(target=_play_siren, daemon=True)
        _siren_thread.start()
        c.log(f"no faces for {elapsed:.1f} attempting to play random siren")


def on_face_found(c):
    global _siren_playing
    
    if _siren_playing:
        _siren_playing = False
        winsound.PlaySound(None, winsound.SND_ASYNC)  # stop
        c.log(f"recieved dispatch context with faces > 0, stopping")


def _play_siren():
    global _siren_playing
    
    while _siren_playing and _sound_files:
        sound_file = random.choice(_sound_files)
        winsound.PlaySound(sound_file, winsound.SND_FILENAME)

def on_stop(c):
    global _siren_playing
    
    _siren_playing = False
    winsound.PlaySound(None, winsound.SND_ASYNC)