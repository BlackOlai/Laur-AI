import os
import time
import threading
import queue
import speech_recognition as sr
from core.status import set_status, is_speaking, get_last_spoken, set_last_spoken

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "input.txt")

# --- FILA THREAD-SAFE DE COMANDOS DO WIDGET ---
# Uma thread dedicada monitora o input.txt e insere comandos aqui.
# A takeCommand consome desta fila com PRIORIDADE MÁXIMA.
_widget_queue = queue.Queue()

def _widget_monitor():
    """Thread dedicada que monitora input.txt a cada 200ms, independente do microfone."""
    print("[STT-Monitor] Thread de monitoramento do chat iniciada.")
    while True:
        try:
            if os.path.exists(INPUT_FILE) and os.path.getsize(INPUT_FILE) > 0:
                with open(INPUT_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # Limpa o arquivo imediatamente para não processar duas vezes
                    with open(INPUT_FILE, "w", encoding="utf-8") as f:
                        f.write("")
                    print(f"[STT-Monitor] Comando do chat detectado: {content[:50]}")
                    _widget_queue.put(content)
        except Exception as e:
            print(f"[STT-Monitor] Erro: {e}")
        time.sleep(0.2)  # Verifica a cada 200ms

# Inicia a thread monitora assim que o módulo é carregado
_monitor_thread = threading.Thread(target=_widget_monitor, daemon=True)
_monitor_thread.start()


def takeCommand(timeout=None, phrase_time_limit=None, return_source=False):
    """
    Lê comando por Voz OU pelo Widget (via fila de prioridade).
    O chat tem SEMPRE prioridade sobre o microfone.
    """
    SKILL_WAIT_FILE = os.path.join(BASE_DIR, "skill_waiting.txt")
    try:
        with open(SKILL_WAIT_FILE, "w", encoding="utf-8") as f:
            f.write("1")
    except: pass

    # --- PRIORIDADE 1: Fila do Widget (processada ANTES de qualquer coisa) ---
    try:
        widget_input = _widget_queue.get_nowait()
        if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
        res = widget_input.lower()
        set_last_spoken("")  # Limpa histórico para evitar falso eco
        print(f"[STT] Consumindo da fila do chat: {res[:60]}")
        return (res, "widget") if return_source else res
    except queue.Empty:
        pass  # Sem mensagens no chat, segue para o microfone

    # --- PRIORIDADE 2: Microfone (com espera de silêncio e verificação contínua da fila) ---

    # Espera a Laura terminar de falar antes de abrir o microfone (anti-eco)
    if is_speaking():
        print("[STT] Aguardando a Laura terminar de falar...")
        start_wait = time.time()
        while is_speaking():
            # DURANTE a espera de fala, verifica a fila do chat a cada 100ms
            try:
                widget_input = _widget_queue.get(timeout=0.1)
                if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
                res = widget_input.lower()
                set_last_spoken("")
                print(f"[STT] Chat recebido DURANTE fala: {res[:60]}")
                return (res, "widget") if return_source else res
            except queue.Empty:
                pass

            # Timeout de segurança anti-deadlock (300s para cobrir listas muito longas)
            if time.time() - start_wait > 300:
                print("[STT] TIMEOUT: Laura travada falando. Forçando idle.")
                set_status("idle", "")
                break

        time.sleep(0.5)  # Pausa pós-fala para dissipar eco no microfone
        print("[STT] Microfone liberado.")

    # Microfone
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.energy_threshold = 300
    r.pause_threshold = 0.6

    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.3)
            set_status("listening", "Estou ouvindo...")
            print("[STT] Ouvindo...")

            audio = None
            listen_start = time.time()
            timeout_reached = False

            while audio is None:
                # Verifica a fila do chat a cada iteração (loop de 1s por chunk de áudio)
                try:
                    widget_input = _widget_queue.get_nowait()
                    if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
                    res = widget_input.lower()
                    set_last_spoken("")
                    print(f"[STT] Chat detectado enquanto ouvia: {res[:60]}")
                    return (res, "widget") if return_source else res
                except queue.Empty:
                    pass

                try:
                    audio = r.listen(source, timeout=1, phrase_time_limit=phrase_time_limit or 10)
                    # Guard anti-eco: descarta áudio capturado enquanto Laura ainda fala
                    if is_speaking():
                        audio = None
                        continue
                except sr.WaitTimeoutError:
                    if timeout and (time.time() - listen_start) >= timeout:
                        timeout_reached = True
                        break
                    continue

            if timeout_reached or audio is None:
                if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
                return ("none", "voice") if return_source else "none"

        set_status("thinking", "Processando voz...")
        query = r.recognize_google(audio, language='pt-BR').lower()

        if len(query) < 2:
            if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
            return ("none", "voice") if return_source else "none"

        print(f"[STT] Reconhecido: {query}")

        # Anti-eco: ignora se for muito parecido com o que a Laura acabou de falar
        last_spoken = get_last_spoken()
        if last_spoken and len(query) > 3:
            if query in last_spoken and len(query) > (len(last_spoken) * 0.6):
                print(f"[STT] Eco detectado. Ignorando.")
                if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
                return ("none", "voice") if return_source else "none"

        if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
        return (query, "voice") if return_source else query

    except sr.UnknownValueError:
        if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
        return ("none", "voice") if return_source else "none"
    except Exception as e:
        print(f"[STT Error] {e}")
        if os.path.exists(SKILL_WAIT_FILE): os.remove(SKILL_WAIT_FILE)
        set_status("idle", "")
        return ("none", "voice") if return_source else "none"
