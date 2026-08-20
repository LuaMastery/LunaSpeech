"""Testes do servidor HTTP e do bot Discord."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HAS_EN_TEST = (REPO / "models" / "en-test" / "test_voice.onnx").exists()


def test_discord_bot_needs_token(monkeypatch):
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    from lunaspeech import discord_bot
    assert discord_bot.main() == 1  # sem token -> erro controlado


@pytest.mark.skipif(not HAS_EN_TEST, reason="modelo en-test ausente")
def test_server_endpoints():
    from lunaspeech import server

    httpd, url = server.serve(voice="en-test", models_dir=str(REPO / "models"))
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    try:
        assert urllib.request.urlopen(url + "/health", timeout=5).read() == b"ok"
        vs = json.loads(urllib.request.urlopen(url + "/voices", timeout=5).read())
        assert any(v["name"] == "en-test" for v in vs)
        # GET /speak -> WAV
        wav = urllib.request.urlopen(url + "/speak?text=hello&voice=en-test", timeout=60).read()
        assert wav[:4] == b"RIFF" and len(wav) > 500
        # POST /speak JSON -> WAV
        req = urllib.request.Request(
            url + "/speak", data=json.dumps({"text": "oi", "voice": "en-test"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        wav2 = urllib.request.urlopen(req, timeout=60).read()
        assert wav2[:4] == b"RIFF"
    finally:
        httpd.shutdown()
