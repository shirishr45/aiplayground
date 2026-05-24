#!/usr/bin/env python3
"""
Local LLM Model Switcher
  Management UI  →  http://localhost:8079
  llama-server   →  http://localhost:8080  (starts when you pick a model)
"""

from __future__ import annotations
import json, os, signal, subprocess, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

HOST      = os.environ.get("HOST",      "127.0.0.1")
PORT      = int(os.environ.get("PORT",      "8080"))
MGMT_PORT = int(os.environ.get("MGMT_PORT", "8079"))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS = [
    {"name": "Qwen3.5-27B  Q4_K_M  (~16GB)",
     "repo": "bartowski/Qwen_Qwen3.5-27B-GGUF:Q4_K_M",
     "ctx":  32768, "extra": ["--reasoning", "off"]},
    {"name": "Qwen3.5-27B  Q8_0    (~28GB, higher quality)",
     "repo": "/Users/shirish/.lmstudio/models/lmstudio-community/Qwen3.5-27B-GGUF/Qwen3.5-27B-Q8_0.gguf",
     "ctx":  32768, "extra": ["--reasoning", "off"]},
    {"name": "Qwen3-32B    Q4_K_M  (~20GB)",
     "repo": "bartowski/Qwen_Qwen3-32B-GGUF:Q4_K_M",
     "ctx":  32768, "extra": ["--reasoning", "off"]},
    {"name": "Qwen3.5-35B-A3B Q4_K_M (~20GB, MoE)",
     "repo": "/Users/shirish/.lmstudio/models/lmstudio-community/Qwen3.5-35B-A3B-GGUF/Qwen3.5-35B-A3B-Q4_K_M.gguf",
     "ctx":  32768, "extra": ["--reasoning", "off"]},
    {"name": "Qwen3.6-35B-A3B Q4_K_M (~20GB, MoE)",
     "repo": "models/Qwen_Qwen3.6-35B-A3B-Q4_K_M.gguf",
     "ctx":  32768, "extra": ["--reasoning", "off"]},
    {"name": "Qwen3-30B-A3B Q4_K_M (~18GB, MoE — fastest)",
     "repo": "bartowski/Qwen_Qwen3-30B-A3B-GGUF:Q4_K_M",
     "ctx":  32768, "extra": ["--reasoning", "off"]},
    {"name": "Qwen3.6-35B-A3B-MTP UD-Q4_K_M (~23GB, MoE, Unsloth)",
     "repo": "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_M",
     "ctx":  32768, "extra": ["--reasoning", "off", "--spec-type", "draft-mtp"]},
    {"name": "Llama-3.3-70B Q4_K_M (~40GB)",
     "repo": "bartowski/Llama-3.3-70B-Instruct-GGUF:Q4_K_M",
     "ctx":  65536, "extra": []},
    {"name": "Hermes-3-Llama-3.1-70B Q4_K_M (~40GB, tool calling)",
     "repo": "NousResearch/Hermes-3-Llama-3.1-70B-GGUF:Q4_K_M",
     "ctx":  32768, "extra": []},
]

# ── State ──────────────────────────────────────────────────────────────────────
_proc: subprocess.Popen | None = None
_current_idx: int | None = None
_status_msg: str = "Select a model to start"
_lock = threading.Lock()


def _model_flag(repo: str) -> list[str]:
    if repo.startswith("/"):
        return ["--model", repo]
    if repo.endswith(".gguf"):
        return ["--model", os.path.join(SCRIPT_DIR, repo)]
    return ["--hf-repo", repo]


def _launch(idx: int) -> None:
    global _proc, _current_idx, _status_msg
    m = MODELS[idx]
    cmd = (["llama-server"]
           + _model_flag(m["repo"])
           + ["--host", HOST, "--port", str(PORT),
              "--ctx-size", str(m["ctx"]),
              "--n-gpu-layers", "999",
              "--threads", "8", "--threads-batch", "8",
              "--batch-size", "512", "--ubatch-size", "256",
              "--flash-attn", "on", "--mlock",
              "--cache-type-k", "q8_0", "--cache-type-v", "q8_0",
              "--jinja"]
           + m["extra"])

    with _lock:
        if _proc and _proc.poll() is None:
            _status_msg = "Stopping previous model…"
            _proc.terminate()
            _proc.wait()
        _status_msg = f"Loading {m['name']}…"
        _current_idx = idx
        # Inherit stdout/stderr so llama-server logs appear in the terminal
        _proc = subprocess.Popen(cmd)

    def _watch() -> None:
        global _status_msg
        if _proc:
            _proc.wait()
            _status_msg = "Process exited (check terminal)"
    threading.Thread(target=_watch, daemon=True).start()


# ── HTTP handler ───────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", ""):
            self._send(200, "text/html; charset=utf-8", _PAGE.encode())
        elif path == "/status":
            running = _proc is not None and _proc.poll() is None
            data = json.dumps({
                "current": _current_idx,
                "name":    MODELS[_current_idx]["name"] if _current_idx is not None else None,
                "running": running,
                "msg":     _status_msg,
            }).encode()
            self._send(200, "application/json", data)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/switch":
            qs  = parse_qs(parsed.query)
            idx = int(qs.get("model", ["0"])[0])
            if 0 <= idx < len(MODELS):
                threading.Thread(target=_launch, args=(idx,), daemon=True).start()
                body = json.dumps({"ok": True}).encode()
                self._send(200, "application/json", body)
            else:
                self.send_error(400)
        else:
            self.send_error(404)

    def log_message(self, *_) -> None:
        pass  # keep terminal clean; llama-server logs are enough


# ── HTML page ──────────────────────────────────────────────────────────────────

def _cards() -> str:
    rows = []
    for i, m in enumerate(MODELS):
        rows.append(
            f'<div class="card" id="c{i}">'
            f'<div class="info"><div class="mn">{m["name"]}</div>'
            f'<div class="mm">ctx {m["ctx"]:,}</div></div>'
            f'<button class="btn" onclick="sw({i})">Load</button></div>'
        )
    return "\n".join(rows)


_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LLM Switcher</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:monospace;background:#111;color:#ccc;padding:28px;max-width:680px}}
h1{{color:#4fc3f7;font-size:1.1rem;margin-bottom:18px}}
#bar{{background:#1e1e1e;border-radius:6px;padding:12px 16px;margin-bottom:18px;
      display:flex;align-items:center;gap:14px}}
#dot{{width:10px;height:10px;border-radius:50%;background:#444;flex-shrink:0}}
#dot.on{{background:#66bb6a}}
#dot.busy{{background:#ffb74d;animation:p 1s infinite}}
@keyframes p{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
#bt{{flex:1;font-size:.88rem}}
#lnk{{color:#4fc3f7;font-size:.82rem;text-decoration:none;white-space:nowrap}}
#lnk:hover{{text-decoration:underline}}
.card{{background:#1e1e1e;border-radius:6px;padding:11px 16px;margin:5px 0;
       display:flex;align-items:center;gap:14px;border:1px solid transparent;
       transition:border-color .15s}}
.card.active{{border-color:#4fc3f7}}
.info{{flex:1}}
.mn{{font-size:.88rem}}
.mm{{color:#555;font-size:.76rem;margin-top:2px}}
.btn{{background:#4fc3f7;color:#000;border:none;padding:5px 14px;border-radius:4px;
      cursor:pointer;font-family:monospace;font-size:.8rem;white-space:nowrap}}
.btn:hover{{background:#81d4fa}}
.btn.cur{{background:#2a3a2a;color:#66bb6a;cursor:default;border:1px solid #66bb6a33}}
</style>
</head>
<body>
<h1>Local LLM — Model Switcher</h1>
<div id="bar">
  <div id="dot"></div>
  <div id="bt">Checking…</div>
  <a id="lnk" href="http://{HOST}:{PORT}" target="_blank">Open chat UI ↗</a>
</div>
{_cards()}
<script>
const N={len(MODELS)};
function sw(i){{
  fetch('/switch?model='+i,{{method:'POST'}}).then(()=>refresh());
}}
function refresh(){{
  fetch('/status').then(r=>r.json()).then(s=>{{
    const dot=document.getElementById('dot');
    const bt=document.getElementById('bt');
    if(s.running){{
      dot.className='on';
      bt.textContent='✓  '+s.name;
    }}else if(s.current!==null){{
      dot.className='busy';
      bt.textContent=s.msg;
    }}else{{
      dot.className='';
      bt.textContent=s.msg;
    }}
    for(let i=0;i<N;i++){{
      const c=document.getElementById('c'+i);
      const b=c.querySelector('.btn');
      if(s.current===i&&s.running){{
        c.classList.add('active');
        b.textContent='Running'; b.className='btn cur';
      }}else{{
        c.classList.remove('active');
        b.textContent='Load'; b.className='btn';
      }}
    }}
  }});
}}
refresh();
setInterval(refresh,4000);
</script>
</body>
</html>"""


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    def _shutdown(sig, frame):
        if _proc and _proc.poll() is None:
            _proc.terminate()
        sys.exit(0)
    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    mgmt_url = f"http://localhost:{MGMT_PORT}"
    print(f"\n  Model Switcher  →  {mgmt_url}")
    print(f"  llama-server    →  http://{HOST}:{PORT}  (starts on first model selection)\n")

    if "--no-browser" not in sys.argv:
        webbrowser.open(mgmt_url)

    try:
        server = HTTPServer(("0.0.0.0", MGMT_PORT), Handler)
    except OSError:
        print(f"  ERROR: port {MGMT_PORT} already in use — is another instance running?")
        print(f"  Kill it with:  lsof -ti :{MGMT_PORT} | xargs kill")
        sys.exit(1)
    server.serve_forever()


if __name__ == "__main__":
    main()
