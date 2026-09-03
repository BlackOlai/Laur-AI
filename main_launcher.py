import webview
import os
import json
import threading
import time
import win32gui
import win32con
import win32api
import psutil
from Laura import main_loop, validate_config

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "status.json")
WIDGET_DATA_FILE = os.path.join(BASE_DIR, "widget_data.json")
WIDGET_HTML = os.path.join(BASE_DIR, "frontend", "widget.html")
INPUT_FILE = os.path.join(BASE_DIR, "input.txt")

class LauraAPI:
    def __init__(self):
        self.window = None

    def resize_window(self, width, height):
        """Redimensiona a janela e aplica transparência por Chroma Key."""
        try:
            import win32gui
            import win32con
            import ctypes

            w, h = int(width), int(height)
            if self.window:
                self.window.resize(w, h)
                print(f"[LauraAPI] Janela redimensionada para {w}x{h}")

            # Captura o HWND
            hwnd = getattr(self, 'hwnd', None)
            if not hwnd:
                hwnd = win32gui.FindWindow(None, 'Laura HUD Evolution')

            if hwnd:
                # 1. Torna a janela "Layered" (permite transparência por cor)
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)

                if w == 200 and h == 200:
                    # 2. MODO BOLINHA: Tudo que for Verde Limão (#00FF00) fica invisível
                    # COLORREF para #00FF00 é 0x0000FF00 (BGR)
                    win32gui.SetLayeredWindowAttributes(hwnd, 0x00FF00, 0, win32con.LWA_COLORKEY)
                    print("[LauraAPI] MODO BOLINHA: Chroma Key VERDE ativado!")
                else:
                    # Modo Normal: Remove o Chroma Key e volta à opacidade total
                    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
                    print("[LauraAPI] Modo normal: Transparência removida.")
            
        except Exception as e:
            print(f"[LauraAPI] Erro no resize/transparência: {e}")


    def move_window(self, dx, dy):
        """Move a janela pela quantidade de pixels delta especificada."""
        try:
            hwnd = win32gui.FindWindow(None, 'Laura HUD Evolution')
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                win32gui.SetWindowPos(hwnd, None, rect[0] + int(dx), rect[1] + int(dy), 0, 0,
                    win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
        except Exception as e:
            print(f"[LauraAPI] Erro ao mover janela: {e}")

    def get_status(self):
        status_data = {"status": "idle", "text": "Laura Online", "mode": "hud"}
        
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    status_data.update(data)
            except: pass
        
        if os.path.exists(WIDGET_DATA_FILE):
            try:
                with open(WIDGET_DATA_FILE, "r", encoding="utf-8") as f:
                    widget_data = json.load(f)
                    status_data.update(widget_data)
            except: pass

        # 1. Verificar se existem erros não lidos
        LOG_FILE = os.path.join(BASE_DIR, "error_logs.json")
        unread_errors = 0
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    unread_errors = sum(1 for e in logs if e.get("status") == "unread")
            except: pass
        status_data["unread_errors"] = unread_errors

        # 2. Adicionar informações de sistema (psutil)
        try:
            status_data["system"] = {
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('C:').percent if os.path.exists('C:') else psutil.disk_usage('/').percent,
                "uptime": int(time.time() - psutil.boot_time()) // 3600 
            }
        except:
            status_data["system"] = {"cpu": 0, "ram": 0, "disk": 0, "uptime": 0}

        return status_data

    def change_mode(self, new_mode):
        try:
            data = self.get_status()
            data["mode"] = new_mode
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            # Notifica o frontend diretamente
            if self.window:
                self.window.evaluate_js(f"applyMode('{new_mode}')")
        except Exception as e:
            print(f"[LauraAPI] Erro em change_mode: {e}")

    def send_message(self, text):
        """Envia mensagem de texto ao Laura via input.txt."""
        try:
            print(f"[LauraAPI] Recebendo mensagem ({len(text)} chars)...")
            with open(INPUT_FILE, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[LauraAPI] Mensagem salva com sucesso.")
            return True
        except Exception as e:
            print(f"[LauraAPI] Erro ao salvar mensagem: {e}")
            return False



def start_unified_laura():
    # Resetar para modo HUD ao iniciar
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["mode"] = "hud"
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except: pass

    # 1. Cérebro em background
    threading.Thread(target=main_loop, daemon=True).start()

    # 2. Interface
    import time
    api = LauraAPI()
    
    window = webview.create_window(
        'Laura HUD Evolution',
        url=WIDGET_HTML + f'?desktop=1&v={time.time()}',
        js_api=api,
        width=350,
        height=650,
        frameless=True,
        on_top=True,
        transparent=False,
        background_color='#00FF00'
    )

    api.window = window

    def on_shown():
        import time as _time
        _time.sleep(0.3)
        found = []
        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h) and ('Laura' in win32gui.GetWindowText(h) or 'HUD' in win32gui.GetWindowText(h)):
                found.append(h)
        win32gui.EnumWindows(enum_cb, None)
        if found:
            api.hwnd = found[0]
            print(f"[Widget] HWND capturado: {api.hwnd} ({win32gui.GetWindowText(api.hwnd)})")
        else:
            api.hwnd = None
            print("[Widget] AVISO: HWND nao encontrado no on_shown.")

    window.events.shown += on_shown

    # Inicia o Widget (debug=False para silenciar os erros no terminal)
    webview.start(debug=False)

if __name__ == '__main__':
    if validate_config():
        start_unified_laura()
