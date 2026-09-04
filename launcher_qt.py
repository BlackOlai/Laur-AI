import sys
import os
import json
import threading
import time
import psutil
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, QObject, Slot, Signal, QTimer
from PySide6.QtWebChannel import QWebChannel
from core.file_processor import extract_text
from Laura import main_loop, validate_config

# Configurações de Caminho (Forçando Absoluto para evitar desencontros)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.abspath(os.path.join(BASE_DIR, "status.json"))
WIDGET_DATA_FILE = os.path.abspath(os.path.join(BASE_DIR, "widget_data.json"))
INPUT_FILE = os.path.abspath(os.path.join(BASE_DIR, "input.txt"))
WIDGET_HTML = os.path.abspath(os.path.join(BASE_DIR, "frontend", "widget.html"))

class Bridge(QObject):
    """Ponte de comunicação entre o HTML (JS) e o Python (IA)."""
    def __init__(self, window):
        super().__init__()
        self.window = window

    @Slot(int, int)
    def resize_window(self, width, height):
        self.window.resize(width, height)
        print(f"[QtAPI] Janela redimensionada para {width}x{height}")

    @Slot(int, int)
    def move_window(self, dx, dy):
        """Move a janela com base no deslocamento do mouse."""
        pos = self.window.pos()
        self.window.move(pos.x() + dx, pos.y() + dy)

    @Slot(result=str)
    def open_file_dialog(self):
        """Abre o diálogo nativo de arquivo (QFileDialog) e envia o conteúdo
        extraído ao Laura via input.txt. Paridade com widget_launcher.py.
        Retorna JSON string (parseado no shim de compatibilidade)."""
        try:
            file_filter = (
                "Arquivos suportados (*.pdf *.docx *.doc *.xlsx *.xls *.csv *.jpg *.png *.webp);;"
                "Documentos (*.pdf *.docx *.doc *.xlsx *.xls *.csv);;"
                "Imagens (*.jpg *.png *.webp)"
            )
            path, _ = QFileDialog.getOpenFileName(self.window, "Anexar arquivo para a Laura", "", file_filter)
            if not path:
                return json.dumps({"success": False, "error": "Nenhum arquivo selecionado."})
            print(f"[QtAPI] Arquivo selecionado: {path}")
            return json.dumps(self._process_uploaded_file(path))
        except Exception as e:
            print(f"[QtAPI] Erro no diálogo de arquivo: {e}")
            return json.dumps({"success": False, "error": str(e)})

    def _process_uploaded_file(self, file_path):
        """Processa o arquivo e envia o conteúdo extraído ao Laura."""
        ext = os.path.splitext(file_path)[1].lower()

        # Imagens: envia comando de visão (o núcleo decide como analisar)
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            prompt = f"[IMAGEM ANEXADA: {file_path}] Por favor, analise esta imagem."
            try:
                with open(INPUT_FILE, "w", encoding="utf-8") as f:
                    f.write(prompt)
                return {"success": True, "filename": os.path.basename(file_path), "type": "IMAGE", "sent": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Documentos: extrai texto e envia para análise
        result = extract_text(file_path)
        if result.get("success"):
            prompt = (
                f"[ARQUIVO ANEXADO: {result['filename']} ({result['type']})]"
                f"\n\nConteúdo do arquivo:\n{result['text']}"
                f"\n\n---\nAnalise o conteúdo acima e me dê um resumo."
            )
            try:
                with open(INPUT_FILE, "w", encoding="utf-8") as f:
                    f.write(prompt)
                result["sent"] = True
            except Exception as e:
                result["sent"] = False
                result["error"] = f"Erro ao enviar para o Laura: {e}"
        return result

    @Slot(result=dict)
    def get_status(self):
        """Retorna o status unificado no formato exato que o HUD (JS) espera."""
        final_data = {
            "mode": "hud", 
            "status": "idle", 
            "text": "",
            "system": {},
            "weather": None,
            "cotacao": None,
            "unread_errors": 0
        }
        
        try:
            # 1. Carrega Status Básico (Modo e Texto da Laura)
            if os.path.exists(STATUS_FILE) and os.path.getsize(STATUS_FILE) > 5:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    try:
                        content = f.read().strip()
                        # Se houver múltiplos objetos JSON, pega apenas o primeiro
                        if content.count('}{') > 0:
                            content = content.split('}{')[0] + '}'
                        final_data.update(json.loads(content))
                    except Exception as je:
                        print(f"[QtAPI] Erro ao ler status.json: {je}")
            
            # 2. Carrega Dados do Widget (Clima, Mercado, etc.)
            if os.path.exists(WIDGET_DATA_FILE) and os.path.getsize(WIDGET_DATA_FILE) > 5:
                with open(WIDGET_DATA_FILE, "r", encoding="utf-8") as f:
                    try:
                        w_content = f.read().strip()
                        widget_data = json.loads(w_content)
                        final_data["weather"] = widget_data.get("weather")
                        final_data["cotacao"] = widget_data.get("cotacao")
                        final_data["news_ia"] = widget_data.get("news_ia")
                    except Exception as je:
                        print(f"[QtAPI] Erro ao ler widget_data.json: {je}")

            # 3. Adiciona Métricas de Sistema (FORMATO CORRETO: final_data["system"])
            final_data["system"] = {
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('C:').percent if os.path.exists('C:') else psutil.disk_usage('/').percent
            }
            
            return final_data
        except Exception as e:
            print(f"[QtAPI] Erro ao unificar status: {e}")
            return final_data

    @Slot(str)
    def send_message(self, text):
        try:
            print(f"[QtAPI] Recebendo mensagem: {text[:20]}...")
            with open(INPUT_FILE, "w", encoding="utf-8") as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"[QtAPI] Erro ao enviar mensagem: {e}")
            return False

    @Slot(str)
    def change_mode(self, new_mode):
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["mode"] = new_mode
                with open(STATUS_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            
            # Notifica o JS
            self.window.view.page().runJavaScript(f"applyMode('{new_mode}')")
        except Exception as e:
            print(f"[QtAPI] Erro ao mudar modo: {e}")

class LauraWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Configurações da Janela (Elite)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |       # Sem bordas
            Qt.WindowType.WindowStaysOnTopHint |     # Sempre no topo
            Qt.WindowType.Tool                        # Não aparece na barra de tarefas (opcional)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # TRANSPARÊNCIA REAL
        
        # 2. Motor do Navegador
        self.view = QWebEngineView(self)
        self.view.page().setBackgroundColor(Qt.GlobalColor.transparent) # Fundo do browser transparente
        self.setCentralWidget(self.view)
        
        # 3. Ponte JS/Python
        self.bridge = Bridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.bridge)
        self.view.page().setWebChannel(self.channel)
        
        # 4. Injeta o código para manter compatibilidade com pywebview
        # Conectamos ao sinal de carregamento da página mas também injetamos via script
        self.view.page().loadFinished.connect(self._inject_compatibility)
        
        # 5. Carrega o HTML
        local_url = QUrl.fromLocalFile(WIDGET_HTML)
        self.view.load(local_url)
        
        # Timer para garantir que os dados atualizem mesmo que o primeiro carregamento falhe
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._force_ui_refresh)
        self.update_timer.start(1000) # Força um refresh a cada 1 segundo (Mais rápido)

        # Tamanho inicial (HUD)
        self.resize(350, 650)
        self.center_window()

    def _force_ui_refresh(self):
        """Força a interface a pedir os dados novamente se estiverem em zero."""
        self.view.page().runJavaScript("if(typeof updateHUD === 'function') updateHUD();")

    def _inject_compatibility(self):
        """Injeta um script que faz o JS achar que ainda está usando o pywebview."""
        js_code = """
        if (typeof QWebChannel !== 'undefined') {
            new QWebChannel(qt.webChannelTransport, function (channel) {
                window.backend = channel.objects.backend;
                // Cria a ponte fake para o pywebview
                window.pywebview = {
                    api: {
                        resize_window: (w, h) => window.backend.resize_window(w, h),
                        move_window: (dx, dy) => window.backend.move_window(dx, dy),
                        open_file_dialog: () => {
                            return new Promise((resolve) => {
                                window.backend.open_file_dialog((result) => {
                                    try { resolve(JSON.parse(result)); }
                                    catch (e) { resolve({"success": false, "error": "resposta inválida do diálogo"}); }
                                });
                            });
                        },
                        send_message: (msg) => {
                            return new Promise((resolve) => {
                                window.backend.send_message(msg, (result) => resolve(result));
                            });
                        },
                        change_mode: (mode) => {
                            return new Promise((resolve) => {
                                window.backend.change_mode(mode, (result) => resolve(result));
                            });
                        },
                        get_status: () => {
                            return new Promise((resolve) => {
                                window.backend.get_status((result) => resolve(result));
                            });
                        }
                    }
                };
                console.log("Qt Bridge Ready - pywebview compatibility injected");
            });
        }
        """
        self.view.page().runJavaScript(js_code)

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        # Move para a ESQUERDA (50 pixels de margem)
        self.move(50, (screen.height() - size.height()) // 2)

def run_qt_launcher():
    app = QApplication(sys.argv)
    
    # Inicia a IA em background com logs detalhados
    print("[SISTEMA] Validando configurações da IA...")
    if validate_config():
        print("[SISTEMA] Configurações OK. Ligando o cérebro da Laura...")
        threading.Thread(target=main_loop, daemon=True).start()
    else:
        print("[ERRO CRÍTICO] Falha na validação das configurações (Laura.py). A IA não iniciará.")
    
    widget = LauraWidget()
    widget.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_qt_launcher()
