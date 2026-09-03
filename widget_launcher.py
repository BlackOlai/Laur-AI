import webview
import os
import json
import time
import threading
import psutil
from core.file_processor import extract_text, get_supported_extensions


# Caminho para o arquivo de estado e o HTML
STATUS_FILE = "status.json"
WIDGET_DATA_FILE = "widget_data.json"
WIDGET_HTML = os.path.abspath(os.path.join("frontend", "widget.html"))

import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input.txt")

class API:
    def __init__(self, window):
        self.window = window

    def resize_window(self, width, height):
        """Redimensiona a janela e aplica formato circular no modo bolinha."""
        try:
            import win32gui
            import win32con
            import ctypes

            # Usa o HWND capturado no evento on_shown (mais confiável)
            hwnd = getattr(self, 'hwnd', None)

            # Fallback: procura pelo título da janela
            if not hwnd:
                hwnd = win32gui.FindWindow(None, 'Laura HUD')
                if hwnd:
                    print(f"[LauraAPI] HWND via FindWindow: {hwnd}")
            else:
                print(f"[LauraAPI] HWND via on_shown: {hwnd}")

            if hwnd:
                w, h = int(width), int(height)
                user32 = ctypes.windll.user32

                # 1. Garante que a janela suporta transparência (Layered Window)
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                                       style | win32con.WS_EX_LAYERED)

                # 2. Redimensiona
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, w, h,
                                      win32con.SWP_NOMOVE | win32con.SWP_SHOWWINDOW)
                print(f"[LauraAPI] Janela redimensionada para {w}x{h}")

                if w == 200 and h == 200:
                    # Modo bolinha: faz o preto puro (#000000) ficar transparente.
                    result = win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 0,
                                                                  win32con.LWA_COLORKEY)
                    print(f"[LauraAPI] MODO BOLINHA: Chroma Key #000000 ativado (resultado={result})")
                else:
                    # Volta ao normal: remove o Chroma Key
                    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
                    print("[LauraAPI] Modo normal: Chroma Key removido.")
            else:
                print("[LauraAPI] Erro: HWND não encontrado. Usando resize padrão.")
                if self.window:
                    self.window.resize(width, height)

        except Exception as e:
            print(f"[LauraAPI] Erro no redimensionamento: {e}")
            import traceback
            traceback.print_exc()


    def move_window(self, dx, dy):
        """Move a janela pela quantidade de pixels delta especificada."""
        try:
            import win32gui
            import win32con
            hwnd = win32gui.FindWindow(None, 'Laura HUD')
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                win32gui.SetWindowPos(hwnd, None, rect[0] + int(dx), rect[1] + int(dy), 0, 0,
                    win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
        except Exception as e:
            print(f"[Widget API] Erro ao mover janela: {e}")

    def get_status(self):
        data = {"status": "idle", "text": "", "mode": "hud"}
        
        # 1. Carregar status básico (status.json)
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data.update(json.load(f))
            except:
                pass
        
        # 2. Carregar dados extras (widget_data.json)
        if os.path.exists(WIDGET_DATA_FILE):
            try:
                with open(WIDGET_DATA_FILE, "r", encoding="utf-8") as f:
                    data.update(json.load(f))
            except:
                pass

        # 4. Verificar erros não lidos
        LOG_FILE = os.path.join(BASE_DIR, "error_logs.json")
        unread_errors = 0
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    unread_errors = sum(1 for e in logs if e.get("status") == "unread")
            except: pass
        data["unread_errors"] = unread_errors

        # 5. Adicionar informações de sistema (psutil)
        try:
            data["system"] = {
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('C:').percent if os.path.exists('C:') else psutil.disk_usage('/').percent,
                "uptime": int(time.time() - psutil.boot_time()) // 3600 
            }
        except:
            data["system"] = {"cpu": 0, "ram": 0, "disk": 0, "uptime": 0}

        return data

    def change_mode(self, new_mode):
        """Chamado pelo JS para salvar a troca manual de modo."""
        data = self.get_status()
        data["mode"] = new_mode
        try:
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"[Widget API] Modo alterado manualmente para: {new_mode}")
            # Notifica o frontend diretamente para garantir a animação
            if self.window:
                self.window.evaluate_js(f"applyMode('{new_mode}')")
        except Exception as e:
            print(f"Erro ao salvar troca manual: {e}")

    def send_message(self, text):
        """Chamado pelo JS para enviar um comando de texto ao Laura."""
        try:
            print(f"[Widget API] Recebendo mensagem ({len(text)} chars)...")
            with open(INPUT_FILE, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[Widget API] Mensagem salva com sucesso.")
            return True
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")
            return False

    def open_file_dialog(self):
        """Abre o diálogo nativo de seleção de arquivo e processa o resultado."""
        try:
            file_types = (
                'Arquivos suportados (*.pdf;*.docx;*.doc;*.xlsx;*.xls;*.csv;*.jpg;*.png;*.webp)',
                'Documentos (*.pdf;*.docx;*.doc;*.xlsx;*.xls;*.csv)',
                'Imagens (*.jpg;*.png;*.webp)'
            )
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types
            )
            if result and len(result) > 0:
                file_path = result[0]
                print(f"[Widget API] Arquivo selecionado: {file_path}")
                return self._process_uploaded_file(file_path)
            return {"success": False, "error": "Nenhum arquivo selecionado."}
        except Exception as e:
            print(f"Erro no diálogo de arquivo: {e}")
            return {"success": False, "error": str(e)}

    def _process_uploaded_file(self, file_path):
        """Processa o arquivo e envia o conteúdo extraído ao Laura."""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Se for imagem, envia comando de visão
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            prompt = f"[IMAGEM ANEXADA: {file_path}] Por favor, analise esta imagem."
            try:
                with open("input.txt", "w", encoding="utf-8") as f:
                    f.write(prompt)
                return {"success": True, "filename": os.path.basename(file_path), "type": "IMAGE", "sent": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Para documentos, continua com a extração de texto
        result = extract_text(file_path)
        if result["success"]:
            prompt = (
                f"[ARQUIVO ANEXADO: {result['filename']} ({result['type']})]"
                f"\n\nConteúdo do arquivo:\n{result['text']}"
                f"\n\n---\nAnalise o conteúdo acima e me dê um resumo."
            )
            try:
                with open("input.txt", "w", encoding="utf-8") as f:
                    f.write(prompt)
                result["sent"] = True
            except Exception as e:
                result["sent"] = False
                result["error"] = f"Erro ao enviar para o Laura: {e}"
        return result

    def move_window(self, x, y):
        """Move a janela para uma posição absoluta."""
        try:
            self.window.move(x, y)
        except Exception as e:
            print(f"Erro ao mover janela: {e}")

    def get_window_pos(self):
        """Retorna a posição atual da janela."""
        try:
            return {"x": self.window.x, "y": self.window.y}
        except Exception as e:
            print(f"Erro ao obter posição: {e}")
            return {"x": 0, "y": 0}


def start_widget():
    # Cria o arquivo de status inicial se não existir
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "w") as f:
            json.dump({"status": "idle", "text": "Laura Online"}, f)

    import time
    import win32api
    api = API(None)
    api.last_mode = "hud"

    # Cria a janela — sem transparência nativa que falha no Win10/11
    window = webview.create_window(
        'Laura HUD',
        # Add query parameter so the frontend can detect desktop mode
        url=WIDGET_HTML + f'?desktop=1&v={time.time()}',
        js_api=api,
        width=350,
        height=650,
        frameless=True,
        on_top=True,
        transparent=True,
        background_color='#000000'
    )

    api.window = window
    api.hwnd = None  # Será preenchido quando a janela aparecer

    def on_shown():
        import win32gui
        import time
        time.sleep(0.3)  # Garante que a janela esteja registrada no SO

        # Varre todas as janelas visíveis para encontrar a Laura HUD
        found = []
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if 'Laura' in title or 'HUD' in title:
                    found.append(hwnd)
        win32gui.EnumWindows(enum_callback, None)

        if found:
            api.hwnd = found[0]
            print(f"[Widget] HWND capturado com sucesso: {api.hwnd} ({win32gui.GetWindowText(api.hwnd)})")
        else:
            print("[Widget] AVISO: Nenhuma janela 'Laura/HUD' encontrada no EnumWindows.")

    window.events.shown += on_shown

    api.window = window
    webview.start(debug=False)


if __name__ == '__main__':
    start_widget()
