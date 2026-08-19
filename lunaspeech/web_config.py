"""Configurações do LunaSpeech via navegador (página HTML local).

Sobe um servidor HTTP mínimo em 127.0.0.1 (porta livre), abre o navegador com
um formulário (tema noturno) e salva as preferências no config ao submeter.
"""

from __future__ import annotations

import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from . import config_store, voices
from . import tone as tone_mod

_HEAD = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🌙 LunaSpeech — Configurações</title>
<style>
  :root { --bg:#0d1117; --panel:#161b22; --acc:#7c5cff; --lunar:#7fdbe8; --gold:#ffd866; --text:#e6edf3; --dim:#8b949e; }
  * { box-sizing:border-box; }
  body { margin:0; background:radial-gradient(1200px 600px at 75% -10%, #182236, var(--bg)); color:var(--text);
         font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif; min-height:100vh; }
  .wrap { max-width:560px; margin:0 auto; padding:42px 20px; }
  h1 { font-weight:600; margin:0 0 18px; }
  h1 small { color:var(--dim); font-size:14px; font-weight:400; }
  .panel { background:var(--panel); border:1px solid #30363d; border-radius:14px; padding:22px; }
  label.lbl { display:block; margin:16px 0 5px; color:var(--lunar); font-size:13px; }
  select, input[type=number] { width:100%; background:#0d1117; color:var(--text); border:1px solid #30363d;
         border-radius:9px; padding:10px 11px; font-size:14px; }
  .row { display:flex; gap:12px; } .row > div { flex:1; }
  .chk { display:flex; align-items:center; gap:10px; margin:14px 0; color:var(--text); }
  .chk input { width:18px; height:18px; accent-color:var(--acc); }
  button { margin-top:20px; width:100%; border:0; border-radius:11px; padding:13px; font-size:15px;
           font-weight:600; cursor:pointer; color:#0d1117; background:linear-gradient(90deg,#6d4aff,#7fdbe8); }
  .ok { color:#3fb950; text-align:center; margin:0 0 12px; font-weight:600; }
  .hint { color:var(--dim); font-size:12px; margin-top:14px; text-align:center; }
</style></head><body><div class="wrap">"""

_FOOT = """</div></body></html>"""


def _form_html(cfg: dict) -> str:
    voice_opts = "".join(
        f'<option value="{n}" {"selected" if n == cfg["voice"] else ""}>'
        f"{n} — {voices.VOICES[n].language}</option>"
        for n in voices.VOICES
    )
    tone_opts = "".join(
        f'<option value="{t}" {"selected" if t == cfg["tone"] else ""}>'
        f"{tone_mod.TONE_LABEL.get(t, t)}</option>"
        for t in tone_mod.ALL_TONES
    )
    au = "checked" if cfg.get("auto_update") else ""
    to = "checked" if cfg.get("test_only") else ""
    saved = '<p class="ok">✓ Configurações salvas! Pode voltar ao terminal.</p>' if cfg.get("_saved") else ""
    return f"""
{saved}
<label class="lbl">Voz padrão</label>
<select name="voice">{voice_opts}</select>
<div class="row">
  <div><label class="lbl">Velocidade (0.5–2.0)</label>
       <input type="number" step="0.05" min="0.5" max="2.0" name="rate" value="{cfg['rate']}"></div>
  <div><label class="lbl">Tom de voz</label><select name="tone">{tone_opts}</select></div>
</div>
<label class="chk"><input type="checkbox" name="auto_update" {au}> Atualização automática ao abrir o painel</label>
<label class="chk"><input type="checkbox" name="test_only" {to}> Modo só teste (toca o áudio sem salvar arquivo)</label>
<button type="submit">💾 Salvar configurações</button>
"""


def page(cfg: dict) -> str:
    body = (
        '<h1>🌙 LunaSpeech <small>configurações</small></h1>'
        '<form method="post" action="/save"><div class="panel">'
        + _form_html(cfg)
        + "</div></form>"
        + '<p class="hint">Salve e volte ao terminal. As preferências valem para o comando e o painel.</p>'
    )
    return _HEAD + body + _FOOT


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send(page(config_store.load()))

    def do_POST(self) -> None:
        if self.path.strip() != "/save":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        data = self.rfile.read(length).decode("utf-8")
        params = parse_qs(data)

        def get(k, default):
            v = params.get(k)
            return v[0] if v else default

        cfg = config_store.load()
        cfg["voice"] = get("voice", cfg["voice"])
        try:
            cfg["rate"] = float(get("rate", cfg["rate"]))
        except (ValueError, TypeError):
            pass
        cfg["tone"] = get("tone", cfg["tone"])
        cfg["auto_update"] = "auto_update" in params
        cfg["test_only"] = "test_only" in params
        config_store.save(cfg)
        cfg["_saved"] = True
        self._send(page(cfg))

    def _send(self, body: str) -> None:
        b = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *args) -> None:  # silencia logs no terminal
        pass


def open_and_serve():
    """Sobe o servidor em porta livre e abre o navegador. Retorna (httpd, url)."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    url = f"http://127.0.0.1:{port}"
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception:
        pass
    return httpd, url
