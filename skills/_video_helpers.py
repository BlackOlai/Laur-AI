# -*- coding: utf-8 -*-
"""Helpers puros de video_explicativo (extraídos en el refactor prompt 09).

Contienen lógica comprobable sin dependencias de red/ffmpeg/LLM:
sanitización, parseo de JSON, conversión de color y medición de duración.
Interfaz preservada: video_explicativo re-importa estas funciones.
"""
import os
import re
import json
import wave
import contextlib
import subprocess


def _sanitize_filename(text):
    text = re.sub(r'laura|criar|crie|cria|gerar|gera|vídeo|vídeos|explicativo|sobre|fazer|faz|um|uma|inema', '', text.lower())
    text = re.sub(r'[^a-z0-9\s]', '', text.strip())
    text = re.sub(r'\s+', '_', text).strip('_')
    return text[:40] if text else "video_projeto"


def load_channel_config(channel_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "quality_guidelines.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("canais", {}).get(channel_id)
    except Exception as e:
        print(f"[VideoExplicativo] Erro ao carregar config: {e}")
        return None


def hex_to_rgb_str(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return f"{int(hex_color[0:2], 16)},{int(hex_color[2:4], 16)},{int(hex_color[4:6], 16)}"
    return "255,195,0"  # Fallback amber


def get_audio_duration(file_path):
    """Mede a duração exata do áudio usando wave (WAV) ou ffprobe (qualquer formato)."""
    if file_path.endswith('.wav') and os.path.exists(file_path):
        try:
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                nchannels = f.getnchannels()
                sampwidth = f.getsampwidth()
                real_size = os.path.getsize(file_path)
                bytes_per_frame = sampwidth * nchannels
                if bytes_per_frame > 0:
                    max_possible = (real_size - 44) // bytes_per_frame
                    if frames > max_possible:
                        frames = max_possible
                dur = round(frames / float(rate), 3)
                if dur < 300:  # Sanity check
                    return dur
        except Exception as _e:
            print(f"[video_explicativo] Falha capturada: {_e}")

    if os.path.exists(file_path):
        try:
            result = subprocess.run(
                f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{file_path}"',
                shell=True, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return round(float(result.stdout.strip()), 3)
        except Exception as e:
            print(f"[VideoExplicativo] ffprobe falhou para {file_path}: {e}")

    print(f"[VideoExplicativo] Arquivo de ├íudio n├úo encontrado ou ileg├¡vel: {file_path}. Usando 5s como fallback.")
    return 5.0


def _sanitize_for_json(text):
    """Converte template literals JS (backticks) para strings JSON seguras."""
    def replace_backtick(m):
        inner = m.group(1)
        inner = inner.replace('\\"', '\\\\"')  # preserve already-escaped quotes
        inner = inner.replace('"', '\\"')
        inner = inner.replace('\n', ' ').replace('\r', '')
        return '"' + inner + '"'
    return re.sub(r'`(.*?)`', replace_backtick, text, flags=re.DOTALL)


def _strip_markdown_fences(text):
    """Remove marcações de bloco de código markdown, incluindo variações."""
    cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned.strip())
    return cleaned.strip()


def _extract_json(text):
    """Extrai e parseia um JSON de uma resposta de texto de forma robusta."""
    cleaned = _strip_markdown_fences(text)

    try:
        return json.loads(cleaned)
    except Exception as _e:
        print(f"[video_explicativo] Falha capturada: {_e}")

    sanitized = _sanitize_for_json(cleaned)
    try:
        return json.loads(sanitized)
    except Exception as e:
        print(f"[VideoExplicativo] Erro ao fazer parse de JSON ap├│s sanitiza├º├úo de backticks: {e}")

    match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
    if match:
        block = match.group(1)
        try:
            return json.loads(block)
        except Exception as _e:
            print(f"[video_explicativo] Falha capturada: {_e}")
        sanitized_block = _sanitize_for_json(block)
        try:
            return json.loads(sanitized_block)
        except Exception as e:
            print(f"[VideoExplicativo] Erro ao fazer parse de JSON extra├¡do por regex: {e}")

    print(f"[VideoExplicativo] Erro de parse JSON geral: todos os m├®todos falharam.")
    return None