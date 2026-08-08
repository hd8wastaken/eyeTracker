import json
import queue
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

NAME = "webserver"
ENABLED = True

PORT = 5000
OPEN_BROWSER = True

_clients = []
_clients_lock = threading.Lock()
_server = None


def _broadcast(payload: str):
    msg = f"data: {payload}\n\n".encode()
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>server</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #111;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: monospace;
    color: #888;
    gap: 14px;
  }
  canvas {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 4px 40px #0009;
    max-width: 95vw;
    max-height: 80vh;
  }
  #status { font-size: 12px; letter-spacing: .08em; }
  #status.lost { color: #e05; }
  #status.tracking { color: #4c4; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="status">connecting...</div>
<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const status = document.getElementById('status');

let target  = [];
let current = [];

function lerp(a, b, t) { return a + (b - a) * t; }

const es = new EventSource('/events');
es.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (canvas.width !== data.win_w)  canvas.width  = data.win_w;
  if (canvas.height !== data.win_h) canvas.height = data.win_h;
  if (current.length !== data.eyes.length) {
    current = data.eyes.map(e => ({ ...e }));
  }
  target = data.eyes;
  if (data.faces > 0) {
    status.className   = 'tracking';
    status.textContent = 'tracking ' + data.faces + ' face(s)';
  } else {
    status.className   = 'lost';
    status.textContent = 'no face detected';
  }
};
es.onerror = () => {
  status.className   = 'lost';
  status.textContent = 'connection lost - is the tracker running?';
};

function drawEye(e) {
  const { cx, cy, r, px, py } = e;
  const pr = r * 0.4;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = '#282828';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(px, py, pr, 0, Math.PI * 2);
  ctx.fillStyle = '#0a0a0a';
  ctx.fill();
  ctx.beginPath();
  ctx.arc(px - pr * 0.35, py - pr * 0.35, Math.max(2, pr / 4), 0, Math.PI * 2);
  ctx.fillStyle = '#fff';
  ctx.fill();
}

function frame() {
  requestAnimationFrame(frame);
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  current.forEach((eye, i) => {
    const t = target[i];
    if (!t) return;
    eye.px = lerp(eye.px, t.px, 0.35);
    eye.py = lerp(eye.py, t.py, 0.35);
    drawEye(eye);
  });
}

frame();
</script>
</body>
</html>"""

_HTML_BYTES = _HTML.encode()


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/events":
            q = queue.Queue(maxsize=4)
            with _clients_lock:
                _clients.append(q)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                while True:
                    msg = q.get(timeout=30)
                    self.wfile.write(msg)
                    self.wfile.flush()
            except Exception:
                pass
            finally:
                with _clients_lock:
                    if q in _clients:
                        _clients.remove(q)
        elif self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(_HTML_BYTES))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(_HTML_BYTES)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_):
        pass


def on_start(c):
    global _server
    try:
        _server = _ThreadingHTTPServer(("0.0.0.0", PORT), _Handler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()
        c.log(f"webserver: http://localhost:{PORT}")
        if OPEN_BROWSER:
            threading.Timer(0.8, lambda: webbrowser.open(f"http://0.0.0.0:{PORT}")).start()
    except OSError as e:
        c.log(f"webserver: failed to bind port {PORT}: {e}")
        _server = None


def on_frame(c):
    _broadcast(json.dumps({
        "faces": c.faces,
        "win_w": c.win_w,
        "win_h": c.win_h,
        "eyes": [
            {"cx": e.cx, "cy": e.cy, "r": e.r, "px": round(e.px, 2), "py": round(e.py, 2)}
            for e in c.eyes
        ],
    }))


def on_stop(c):
    global _server
    if _server:
        _server.shutdown()
        _server = None
        c.log("webserver: stopped")
