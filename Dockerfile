# LunaSpeech — imagem para publicar o site/API em qualquer plataforma
# (Render, Hugging Face Spaces, Koyeb, Fly.io, etc.)
FROM python:3.11-slim

WORKDIR /app

# instala o LunaSpeech a partir do código do repositório + fonetização (espeak-ng embutido)
COPY . .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir ".[phonemize]"

# baixa a voz pt-BR (faber) já no build (deixa o início mais rápido)
RUN python -c "from lunaspeech import voices; voices.ensure_voice('faber')" || true

# containers precisam escutar em 0.0.0.0; a porta vem de $PORT (Render/HF/Koyeb)
ENV LUNASPEECH_HOST=0.0.0.0
EXPOSE 8000

CMD ["lunaspeech", "serve"]
