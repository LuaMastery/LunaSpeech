"""Servidor HTTP do LunaSpeech — API + player web (stdlib, sem dependências novas).

Expõe:
  GET  /                    → player web (digite texto e ouça no navegador)
  GET  /speak?text=...      → áudio WAV  (voice, rate, tone opcionais)
  POST /speak  {text,...}   → áudio WAV (JSON)
  GET  /voices             → JSON com as vozes disponíveis
  GET  /health             → "ok"

Qualquer sistema (Discord, automação, outra página) pode chamar /speak.
"""

from __future__ import annotations

import io
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__, voices as voices_mod
from . import tone as tone_mod

_PLAYER = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🌙 LunaSpeech</title>
<style>
  :root{--bg:#0d1117;--panel:#161b22;--acc:#7c5cff;--lunar:#7fdbe8;--gold:#ffd866;--text:#e6edf3;--dim:#8b949e}
  *{box-sizing:border-box}
  body{margin:0;background:radial-gradient(1200px 600px at 75% -10%,#182236,var(--bg));color:var(--text);
       font:15px/1.55 system-ui,sans-serif;min-height:100vh;display:flex;justify-content:center;padding:30px 16px}
  .card{width:100%;max-width:620px;background:var(--panel);border:1px solid #30363d;border-radius:16px;padding:26px}
  h1{margin:0 0 4px;font-weight:600}
  small{color:var(--dim)}
  textarea{width:100%;min-height:110px;background:#0d1117;color:var(--text);border:1px solid #30363d;
           border-radius:10px;padding:12px;font:15px/1.5 inherit;resize:vertical}
  .row{display:flex;gap:10px;margin:12px 0}
  .row>div{flex:1}
  label{display:block;color:var(--lunar);font-size:12px;margin:0 0 4px}
  select,input[type=range]{width:100%;background:#0d1117;color:var(--text);border:1px solid #30363d;border-radius:8px;padding:8px}
  button{width:100%;border:0;border-radius:11px;padding:13px;font-size:15px;font-weight:600;cursor:pointer;
         color:#0d1117;background:linear-gradient(90deg,#6d4aff,#7fdbe8);margin-top:6px}
  button:disabled{opacity:.6}
  audio{width:100%;margin-top:14px}
  .hint{color:var(--dim);font-size:12px;margin-top:14px;text-align:center}
</style></head><body><div class="card">
  <h1>🌙 LunaSpeech <small id="v"></small></h1>
  <textarea id="t" placeholder="Digite o texto para falar...">Olá! Eu sou o LunaSpeech.</textarea>
  <div class="row"><div><label>Voz</label><select id="voice"></select></div>
    <div><label>Tom</label><select id="tone"></select></div></div>
  <div class="row"><div><label>Velocidade: <span id="rv">1.00×</span></label>
    <input type="range" id="rate" min="0.5" max="2" step="0.05" value="1"></div></div>
  <button id="b" onclick="falar()">🔊 Falar</button>
  <audio id="a" controls></audio>
  <p class="hint">API: <code>GET /speak?text=...</code> &nbsp;•&nbsp; <code>POST /speak</code> JSON</p>
</div>
<script>
const $=id=>document.getElementById(id);
fetch('/voices').then(r=>r.json()).then(vs=>{
  const s=$('voice'); vs.forEach(v=>{const o=document.createElement('option');o.value=v.name;
    o.textContent=v.name+' '+v.language;if(v.default)o.selected=true;s.appendChild(o);});
  $('v').textContent='· '+vs.length+' vozes';
});
fetch('/tones').then(r=>r.json()).then(ts=>{const s=$('tone');
  ts.forEach(t=>{const o=document.createElement('option');o.value=t.value;o.textContent=t.label;s.appendChild(o);});});
$('rate').oninput=e=>$('rv').textContent=parseFloat(e.target.value).toFixed(2)+'×';
async function falar(){
  const p=new URLSearchParams({text:$('t').value,voice:$('voice').value,
    rate:$('rate').value,tone:$('tone').value});
  const b=$('b');b.disabled=true;b.textContent='sintetizando...';
  try{const r=await fetch('/speak?'+p);if(!r.ok){alert('Erro ao sintetizar');return;}
    const blob=await r.blob();const a=$('a');a.src=URL.createObjectURL(blob);a.play();}
  finally{b.disabled=false;b.textContent='🔊 Falar';}
}
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    models_dir = None
    _tts_cache: dict = {}

    def _get_tts(self, voice):
        if voice not in self._tts_cache:
            from .core import LunaSpeech
            self._tts_cache[voice] = LunaSpeech(voice=voice, models_dir=self.models_dir)
        return self._tts_cache[voice]

    def _send_bytes(self, data, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj, code=200):
        self._send_bytes(json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8", code)

    def _speak(self, text, voice, rate, tone):
        import soundfile as sf
        from .audio import normalize_peak
        tts = self._get_tts(voice or voices_mod.DEFAULT_VOICE)
        result = tts.synthesize(text, rate=rate or 1.0, tone=tone or "auto")
        buf = io.BytesIO()
        sf.write(buf, normalize_peak(result.audio), result.sample_rate, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    def do_GET(self):
        path = urlparse(self.path).path
        qs = parse_qs(urlparse(self.path).query)
        if path == "/":
            self._send_bytes(_PLAYER.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/health":
            self._send_bytes(b"ok", "text/plain")
        elif path == "/voices":
            self._send_json([{"name": n, "language": s.language, "default": n == voices_mod.DEFAULT_VOICE}
                             for n, s in voices_mod.VOICES.items()])
        elif path == "/tones":
            self._send_json([{"value": t, "label": tone_mod.TONE_LABEL.get(t, t)}
                             for t in tone_mod.ALL_TONES])
        elif path == "/speak":
            text = (qs.get("text", [""])[0])
            if not text.strip():
                self._send_json({"error": "parâmetro 'text' vazio"}, 400)
                return
            try:
                wav = self._speak(text, qs.get("voice", [None])[0],
                                  float(qs.get("rate", ["1"])[0]),
                                  qs.get("tone", ["auto"])[0])
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, 500)
                return
            self._send_bytes(wav, "audio/wav")
        else:
            self._send_json({"error": "não encontrado"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/speak":
            self._send_json({"error": "não encontrado"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError:
            data = {k: v[0] for k, v in parse_qs(raw).items()}
        text = (data.get("text") or "").strip()
        if not text:
            self._send_json({"error": "'text' vazio"}, 400)
            return
        try:
            wav = self._speak(text, data.get("voice"), float(data.get("rate", 1.0)),
                              data.get("tone", "auto"))
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, 500)
            return
        self._send_bytes(wav, "audio/wav")

    def log_message(self, *args):
        pass


def serve(host: str = "127.0.0.1", port: int = 0, voice=None, models_dir=None):
    """Sobe o servidor. Retorna (httpd, url). voice só pré-aquece o cache."""
    _Handler.models_dir = models_dir
    if voice:
        _Handler._tts_cache = {}  # o cache é preenchido por requisição
    if port == 0:
        s = socket.socket()
        s.bind((host, 0))
        port = s.getsockname()[1]
        s.close()
    httpd = ThreadingHTTPServer((host, port), _Handler)
    return httpd, f"http://{host}:{port}"
