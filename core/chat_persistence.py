"""Persistencia del histórico de chat de la Laura (extraído de Laura.py).

Graba chat_history.json (últimos 60 turnos) para que la HUD pueda
restaurar el panel de conversación al reabrir. Lee/estilo del core.
"""
import os
import json
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
MAX_TURNS = 60  # 120 entradas (user+ai)


def persist_chat_history(user_text, ai_text):
    """Graba el turno actual en chat_history.json (50 turnos)."""
    try:
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.append({
            "role": "user", "content": str(user_text)[:500],
            "ts": datetime.datetime.now().strftime("%H:%M"),
        })
        history.append({
            "role": "ai", "content": str(ai_text)[:1500],
            "ts": datetime.datetime.now().strftime("%H:%M"),
        })
        history = history[-MAX_TURNS * 2:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ChatHistory] Error al persistir: {e}")