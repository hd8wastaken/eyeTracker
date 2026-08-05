import os
import sys
import time
import threading
import subprocess

NAME = "siren"
ENABLED = False

GRACE = 1.5
REPEAT = 2.5

_wav = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "assets", "siren.wav")
_lost_at = None
_last_play = 0.0
_log = None


def _play():
    if not os.path.isfile(_wav):
        print("\a", end="", flush=True)
        return
    try:
        if os.name == "nt":
            import winsound
            winsound.PlaySound(_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            cmd = ["afplay", _wav] if sys.platform == "darwin" else ["aplay", "-q", _wav]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("\a", end="", flush=True)


def _stop():
    if os.name == "nt":
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass


def on_start(c):
    global _log
    _log = c.log
    if not os.path.isfile(_wav):
        _log(f"siren: no wav at {_wav}, falling back to terminal bell")


def on_face_lost(c):
    global _lost_at, _last_play
    now = time.time()
    if _lost_at is None:
        _lost_at = now
        return
    if now - _lost_at < GRACE:
        return
    if now - _last_play < REPEAT:
        return
    _last_play = now
    threading.Thread(target=_play, daemon=True).start()
    if _log:
        _log(f"siren: face gone for {now - _lost_at:.1f}s")


def on_face_found(c):
    global _lost_at, _last_play
    if _lost_at is not None and time.time() - _lost_at >= GRACE:
        _stop()
        if _log:
            _log("siren: face back, alarm off")
    _lost_at = None
    _last_play = 0.0


def on_stop(c):
    _stop()
