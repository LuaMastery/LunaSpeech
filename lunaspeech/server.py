"""Servidor HTTP do LunaSpeech — site + API (stdlib, sem dependências novas).

Site (player completo):  GET /
API:                      GET/POST /speak  → WAV
                          GET /voices, /tones, /health
"""

from __future__ import annotations

import io
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__, voices as voices_mod
from . import tone as tone_mod

_SITE = """<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🌙 LunaSpeech — voz da lua</title>
<style>
:root{--bg:#0a0e17;--panel:#131a26;--panel2:#1b2333;--acc:#7c5cff;--lunar:#7fdbe8;
      --gold:#ffd866;--text:#e6edf3;--dim:#8b97a8;--line:#263042}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font:16px/1.6 'Segoe UI',system-ui,sans-serif;
     overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;z-index:-2;
  background:radial-gradient(900px 500px at 80% -10%,#1a2540,transparent),
             radial-gradient(700px 400px at 10% 110%,#1a1a3a,transparent)}
.stars{position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.5;
  background-image:radial-gradient(1px 1px at 20% 30%,#fff,transparent),
    radial-gradient(1px 1px at 60% 70%,#ffd866,transparent),
    radial-gradient(1px 1px at 80% 20%,#7fdbe8,transparent),
    radial-gradient(1px 1px at 40% 80%,#fff,transparent),
    radial-gradient(1px 1px at 90% 60%,#fff,transparent);background-size:100% 100%}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header{position:sticky;top:0;z-index:10;backdrop-filter:blur(10px);
  background:rgba(10,14,23,.75);border-bottom:1px solid var(--line)}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:62px}
.logo{font-size:20px;font-weight:700}
.logo .grad{background:linear-gradient(90deg,#7c5cff,#7fdbe8);-webkit-background-clip:text;
  background-clip:text;color:transparent}
nav a{color:var(--dim);text-decoration:none;margin-left:22px;font-size:14px}
nav a:hover{color:var(--text)}
.hero{text-align:center;padding:64px 0 32px}
.hero h1{font-size:clamp(40px,8vw,76px);font-weight:800;letter-spacing:-1px;line-height:1}
.hero h1 .grad{background:linear-gradient(90deg,#9d7bff,#7fdbe8,#ffd866);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--dim);font-size:18px;margin-top:14px}
.badges{margin-top:18px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.badges span{background:var(--panel);border:1px solid var(--line);color:var(--lunar);
  padding:5px 12px;border-radius:999px;font-size:12px}
.player{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);
  border-radius:18px;padding:24px;max-width:680px;margin:36px auto;box-shadow:0 20px 60px rgba(0,0,0,.4)}
textarea{width:100%;min-height:96px;background:#0a0e17;color:var(--text);border:1px solid var(--line);
  border-radius:12px;padding:14px;font:inherit;resize:vertical}
.row{display:flex;gap:12px;margin:14px 0 0;flex-wrap:wrap}
.row>div{flex:1;min-width:130px}
label{display:block;color:var(--lunar);font-size:12px;margin:0 0 5px}
select,input[type=range]{width:100%;background:#0a0e17;color:var(--text);border:1px solid var(--line);
  border-radius:9px;padding:9px 10px;font:inherit}
button{border:0;border-radius:12px;padding:13px 20px;font:inherit;font-weight:700;cursor:pointer;
  color:#0a0e17;background:linear-gradient(90deg,#7c5cff,#7fdbe8);transition:transform .1s}
button:hover{transform:translateY(-1px)}
button:disabled{opacity:.55;cursor:wait}
.actions{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}
audio{width:100%;margin-top:12px;height:38px}
.dl{color:var(--lunar);font-size:13px;text-decoration:none;border:1px solid var(--line);
  padding:9px 14px;border-radius:9px}
.dl:hover{background:var(--panel2)}
section{padding:56px 0}
.sec-title{text-align:center;font-size:28px;font-weight:700;margin-bottom:8px}
.sec-sub{text-align:center;color:var(--dim);margin-bottom:32px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px;
  transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--acc);transform:translateY(-3px)}
.card .ico{font-size:26px}
.card h3{font-size:17px;margin:10px 0 6px}
.card p{color:var(--dim);font-size:14px}
.vcard{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;
  cursor:pointer;text-align:center;transition:all .15s}
.vcard:hover,.vcard.sel{border-color:var(--lunar);background:var(--panel2)}
.vcard .nm{font-weight:700}
.vcard .lg{color:var(--dim);font-size:13px}
.vcard .go{color:var(--lunar);font-size:12px;margin-top:6px;visibility:hidden}
.vcard:hover .go{visibility:visible}
footer{border-top:1px solid var(--line);padding:28px 0;text-align:center;color:var(--dim);font-size:13px}
footer a{color:var(--lunar);text-decoration:none}
.hint{color:var(--dim);font-size:12px;text-align:center;margin-top:10px}
code{background:#0a0e17;padding:2px 6px;border-radius:5px;font-size:13px;color:var(--gold)}
@media(max-width:560px){nav{display:none}}
</style></head><body><div class="stars"></div>

<header><div class="wrap">
  <div class="logo">🌙 <span class="grad">LunaSpeech</span></div>
  <nav><a href="#testar">Testar</a><a href="#recursos">Recursos</a><a href="#vozes">Vozes</a></nav>
</div></header>

<div class="wrap">
<section class="hero" id="testar">
  <h1><span class="grad">LunaSpeech</span></h1>
  <p>voz da lua • text-to-speech em português, leve e open source</p>
  <div class="badges">
    <span>🇧🇷 Pt-BR</span><span>🎭 Tom emocional</span><span>🔤 Soletração</span>
    <span>💻 Roda em CPU</span><span>🔌 API + Discord</span>
  </div>
  <div class="player">
    <textarea id="t" placeholder="Digite o texto para a Luna falar...">Olá! Eu sou a LunaSpeech, a voz da lua. Escreva qualquer texto e eu falo pra você.</textarea>
    <div class="row">
      <div><label>Voz</label><select id="voice"></select></div>
      <div><label>Tom de voz</label><select id="tone"></select></div>
      <div><label>Velocidade · <span id="rv">1.00×</span></label>
        <input type="range" id="rate" min="0.5" max="2" step="0.05" value="1"></div>
    </div>
    <div class="row">
      <div><label>Soletração</label><select id="spell">
        <option value="auto">automática (só o que precisar)</option>
        <option value="on">sempre (soletra TODO o texto)</option>
        <option value="off">nunca soletrar</option></select></div>
      <div><label>Versão</label><select id="mode">
        <option value="flash">⚡ Flash (rápida)</option>
        <option value="thinking">🧠 Thinking (aprimorada)</option></select></div>
    </div>
    <div class="actions">
      <button id="b" onclick="falar()">🔊 Falar</button>
      <a class="dl" id="dl" href="#" style="display:none">⬇ Baixar .wav</a>
    </div>
    <audio id="a" controls></audio>
    <p class="hint">Dica: texto amigável fica calmo; texto raivoso fica tenso. Experimente:
      <code>EU ODEIO ESPERAR!!!</code></p>
  </div>
</section>

<section id="recursos">
  <div class="sec-title">Recursos</div>
  <div class="sec-sub">tudo que a Luna faz — teste no player acima</div>
  <div class="grid">
    <div class="card"><div class="ico">🇧🇷</div><h3>Português do Brasil</h3>
      <p>Entende números, <code>R$ 1.234,56</code>, datas, horas, siglas e abreviações.</p></div>
    <div class="card"><div class="ico">🎭</div><h3>Tom emocional</h3>
      <p>Deteca a emoção do texto — amigável, alegre, raivoso, triste — e ajusta a prosódia.</p></div>
    <div class="card"><div class="ico">🔤</div><h3>Soletração</h3>
      <p>Soletra siglas (CPF) e palavras estrangeiras sem falhas.</p></div>
    <div class="card"><div class="ico">⚡</div><h3>Leve e em CPU</h3>
      <p>Sem GPU, sem PyTorch. Roda até num Raspberry Pi.</p></div>
    <div class="card"><div class="ico">🎚️</div><h3>Vozes e controle</h3>
      <p>Várias vozes pt-BR, controle de velocidade e tom.</p></div>
    <div class="card"><div class="ico">🔌</div><h3>Integrações</h3>
      <p>API <code>/speak</code> e bot de Discord pra usar em qualquer lugar.</p></div>
  </div>
</section>

<section id="vozes">
  <div class="sec-title">Vozes</div>
  <div class="sec-sub">clique numa voz pra testá-la no player</div>
  <div class="grid" id="vgrid"></div>
</section>
</div>

<footer><div class="wrap">
  🌙 LunaSpeech v__VERSION__ · open source · <a href="https://github.com/LuaMastery/LunaSpeech">GitHub</a>
</div></footer>

<script>
const $=id=>document.getElementById(id);
async function load(){
  const vs=await fetch('/voices').then(r=>r.json());
  const sel=$('voice');
  vs.forEach(v=>{const o=document.createElement('option');o.value=v.name;
    o.textContent=v.name+' · '+v.language;if(v.default){o.selected=true;sel.value=v.name;}sel.appendChild(o);});
  const grid=$('vgrid');
  vs.forEach(v=>{const c=document.createElement('div');c.className='vcard';c.dataset.name=v.name;
    c.innerHTML='<div class="nm">'+v.name+'</div><div class="lg">'+v.language+(v.default?' · padrão':'')+
    '</div><div class="go">▶ usar esta voz</div>';
    c.onclick=()=>{$('voice').value=v.name;[...grid.children].forEach(x=>x.classList.remove('sel'));
      c.classList.add('sel');$('t').value='Olá! Eu sou a voz '+v.name+'.';window.scrollTo({top:0,behavior:'smooth'});};
    grid.appendChild(c);});
  const ts=await fetch('/tones').then(r=>r.json());
  ts.forEach(t=>{const o=document.createElement('option');o.value=t.value;o.textContent=t.label;
    if(t.value==='auto')o.selected=true;$('tone').appendChild(o);});
}
$('rate').oninput=e=>$('rv').textContent=parseFloat(e.target.value).toFixed(2)+'×';
async function falar(){
  const p=new URLSearchParams({text:$('t').value,voice:$('voice').value,
    rate:$('rate').value,tone:$('tone').value,spell:$('spell').value,mode:$('mode').value});
  const b=$('b');b.disabled=true;b.textContent='sintetizando...';
  try{const r=await fetch('/speak?'+p);if(!r.ok){const e=await r.json().catch(()=>({}));alert('Erro: '+(e.error||r.status));return;}
    const blob=await r.blob();const url=URL.createObjectURL(blob);const a=$('a');a.src=url;a.play();
    const dl=$('dl');dl.href='/speak?'+p.toString();dl.style.display='inline-block';}
  finally{b.disabled=false;b.textContent='🔊 Falar';}
}
load();
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

    def _speak(self, text, voice, rate, tone, spell="auto", mode="flash"):
        import soundfile as sf
        from .audio import normalize_peak
        from .text.numbers import should_spell, spell_words
        if spell == "on" or (spell == "auto" and should_spell(text)):
            text = spell_words(text)
        tts = self._get_tts(voice or voices_mod.DEFAULT_VOICE)
        result = tts.synthesize(text, rate=rate or 1.0, tone=tone or "auto",
                                mode=mode or "flash")
        buf = io.BytesIO()
        sf.write(buf, normalize_peak(result.audio), result.sample_rate, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    def do_GET(self):
        path = urlparse(self.path).path
        qs = parse_qs(urlparse(self.path).query)
        if path == "/":
            self._send_bytes(_SITE.replace("__VERSION__", __version__).encode("utf-8"),
                             "text/html; charset=utf-8")
        elif path == "/health":
            self._send_bytes(b"ok", "text/plain")
        elif path == "/voices":
            self._send_json([{"name": n, "language": s.language, "default": n == voices_mod.DEFAULT_VOICE}
                             for n, s in voices_mod.VOICES.items()])
        elif path == "/tones":
            self._send_json([{"value": t, "label": tone_mod.TONE_LABEL.get(t, t)}
                             for t in tone_mod.ALL_TONES])
        elif path == "/speak":
            text = qs.get("text", [""])[0]
            if not text.strip():
                self._send_json({"error": "parâmetro 'text' vazio"}, 400)
                return
            try:
                wav = self._speak(text, qs.get("voice", [None])[0],
                                  float(qs.get("rate", ["1"])[0]), qs.get("tone", ["auto"])[0],
                                  qs.get("spell", ["auto"])[0], qs.get("mode", ["flash"])[0])
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
                              data.get("tone", "auto"), data.get("spell", "auto"),
                              data.get("mode", "flash"))
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, 500)
            return
        self._send_bytes(wav, "audio/wav")

    def log_message(self, *args):
        pass


def serve(host: str = "127.0.0.1", port: int = 0, voice=None, models_dir=None):
    """Sobe o servidor (site + API). Retorna (httpd, url)."""
    _Handler.models_dir = models_dir
    if port == 0:
        s = socket.socket()
        s.bind((host, 0))
        port = s.getsockname()[1]
        s.close()
    httpd = ThreadingHTTPServer((host, port), _Handler)
    return httpd, f"http://{host}:{port}"
