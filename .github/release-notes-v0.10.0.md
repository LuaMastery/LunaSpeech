# 🌙 LunaSpeech v0.10.0 — atualização com reinício automático 🔄

## 🆕 O que mudou
Quando o Luna detecta uma nova versão, agora ele **se atualiza, fecha o processo antigo e reinicia sozinho** — no mesmo terminal, já na versão nova. Não precisa mais reiniciar manualmente.

- Funciona na **atualização automática** (ao abrir o painel) e na **manual** (Buscar atualizações → Sim).
- O painel reabre automaticamente após a atualização.
- **Guarda anti-loop**: se a versão nova não "pegar" por algum motivo, o Luna não fica reiniciando infinitamente — avisa pra reiniciar manualmente.
- Cursor e estado do terminal são restaurados antes do reinício.

## ▶️ Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.10.0"
lunaspeech
```
(A partir desta versão, as próximas atualizações são sozinhas: é só abrir o painel. 🌙)

Full changelog: compare com [v0.9.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.9.1).
