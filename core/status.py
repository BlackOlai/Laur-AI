import os
import json
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(BASE_DIR, "status.json")

status_lock = threading.Lock()

# Variáveis globais para controle de voz (Thread-Safe)
_SPEAKING_THREADS = 0
_LAST_SPOKEN_TEXT = ""
_THREADS_LOCK = threading.Lock()

def is_speaking():
    """Retorna True se houver qualquer thread de voz ativa."""
    with _THREADS_LOCK:
        return _SPEAKING_THREADS > 0

def set_last_spoken(text):
    """Armazena o último texto falado pela Laura."""
    global _LAST_SPOKEN_TEXT
    with _THREADS_LOCK:
        _LAST_SPOKEN_TEXT = (text or "").lower().strip()

def clear_last_spoken():
    """Limpa o histórico de fala (usado ao receber input do chat)."""
    global _LAST_SPOKEN_TEXT
    with _THREADS_LOCK:
        _LAST_SPOKEN_TEXT = ""

def get_last_spoken():
    """Retorna o último texto falado para comparação."""
    with _THREADS_LOCK:
        return _LAST_SPOKEN_TEXT

def set_status(status, text="", **kwargs):
    """
    Atualiza o estado global da Laura para o Widget e controla o contador de voz.
    Suporta parâmetros extras (como mode='chat') via kwargs.
    """
    global _SPEAKING_THREADS
    
    with _THREADS_LOCK:
        if status == "speaking":
            _SPEAKING_THREADS += 1
        elif status == "idle" and _SPEAKING_THREADS > 0:
            _SPEAKING_THREADS -= 1
            
    with status_lock:
        try:
            # Se ainda houver threads falando, mantém o status visual como 'speaking'
            effective_status = status
            if status == "idle" and is_speaking():
                effective_status = "speaking"

            # Prepara os dados básicos
            data = {"status": effective_status, "text": text}
            
            # Adiciona parâmetros extras (como 'mode')
            data.update(kwargs)
            
            if os.path.exists(STATUS_FILE):
                try:
                    with open(STATUS_FILE, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            current_data = json.loads(content)
                            if isinstance(current_data, dict):
                                # Preserva o que já estava no arquivo e atualiza com os novos dados
                                current_data.update(data)
                                data = current_data
                except: pass
            
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                try: os.fsync(f.fileno())
                except: pass
                
        except Exception as e:
            print(f"[Status Error] {e}")
