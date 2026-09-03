import os
import asyncio
import subprocess
import edge_tts
import json
import threading
import random
import string
import time

# Tenta importar pygame para reprodução robusta
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
    print("[TTS] Pygame Mixer inicializado com sucesso.")
except Exception as e:
    HAS_PYGAME = False
    print(f"[TTS Warning] Pygame Mixer falhou: {e}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(BASE_DIR, "status.json")
PROFILE_FILE = os.path.join(BASE_DIR, "profile.json")

def set_status(status, text=""):
    try:
        from core.status import set_status as update_status
        update_status(status, text)
    except:
        pass

def get_current_voice():
    default_voice = "pt-BR-ThalitaMultilingualNeural"
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
                v = profile.get("voice", default_voice)
                return v
        except: pass
    return default_voice

# ---------------------------------------------------------------------------
# Edge-TTS (online)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Edge-TTS (online)
# ---------------------------------------------------------------------------

async def _generate_audio_edge(text, voice, file_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(file_path)

# ---------------------------------------------------------------------------
# Reprodução de Áudio
# ---------------------------------------------------------------------------

def _play_audio(file_path):
    # Método 1: Pygame
    if HAS_PYGAME:
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            return True
        except Exception as e:
            print(f"[TTS] Pygame Play Error: {e}")

    # Método 2: PowerShell (WMPlayer)
    try:
        ps_command = (
            f"$m = New-Object -ComObject WMPlayer.OCX; "
            f"$m.settings.volume = 100; "
            f"$m.URL = '{file_path}'; "
            f"$m.controls.play(); "
            f"while($m.playState -ne 1) {{ Start-Sleep -m 100 }}; "
            f"$m.close();"
        )
        os.system(f'powershell -c "{ps_command}" >nul 2>&1')
        return True
    except Exception as e:
        print(f"[TTS] PowerShell Play Error: {e}")
        return False

# ---------------------------------------------------------------------------
# Roteador Principal de Síntese de Voz
# ---------------------------------------------------------------------------

async def _speak_process(text):
    rand_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    voice = get_current_voice()
    print(f"[TTS] Falando: '{text[:60]}...' via {voice}")

    # --- Edge-TTS (online, voz padrão ou selecionada pelo usuário) ---
    temp_file = os.path.abspath(os.path.join(BASE_DIR, f"temp_speech_{rand_id}.mp3"))
    try:
        await _generate_audio_edge(text, voice, temp_file)

        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            raise Exception("Arquivo de audio nao foi gerado.")

        if not _play_audio(temp_file):
            raise Exception("Todos os metodos de audio falharam.")

    except Exception as e:
        print(f"[TTS Error] {e}")
        # Fallback Final: SAPI5 (Windows nativo, sem dependências externas)
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
        except: pass
    finally:
        if os.path.exists(temp_file):
            try: os.remove(temp_file)
            except: pass

# ---------------------------------------------------------------------------
# Lock global para impedir falas sobrepostas
# ---------------------------------------------------------------------------
PLAYBACK_LOCK = threading.Lock()

def say(text):
    if not text: return
    # Limpa tags markdown ou estranhas para não serem lidas
    clean_text = text.replace("**", "").replace("#", "").strip()

    # Armazena para evitar eco (Laura não responder a si mesma)
    try:
        from core.status import set_last_spoken
        set_last_spoken(clean_text)
    except: pass

    set_status("speaking", clean_text)
    print(f"Laura: {clean_text}")

    def run():
        with PLAYBACK_LOCK:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_speak_process(clean_text))
            finally:
                set_status("idle", "")
                loop.close()

    threading.Thread(target=run, daemon=True).start()
