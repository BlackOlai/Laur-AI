"""Sistema de log de errores de la Laura (extraído de Laura.py — refactor prompt 09).

Registra errores en error_logs.json marcados como "unread" para que la HUD
pueda mostrarlos (badge ANOMALY / borde rojo).
"""
import os
import json
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "error_logs.json")


def log_system_error(origin, error):
    """Registra un error con origen y marca "unread" (visible en la HUD)."""
    try:
        log_file = LOG_FILE
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        logs.append({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origin": origin, "message": str(error), "status": "unread"
        })
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"[SystemLog] Error interno al guardar: {e}")