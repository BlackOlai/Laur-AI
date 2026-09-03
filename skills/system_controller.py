import os
import subprocess
import pyautogui
import time
import pygetwindow as gw

KEYWORDS = [
    "controle", "sistema", "abrir", "fechar", "volume", "mudo",
    "brilho", "teclado", "mouse", "print", "screenshot", "desligar",
    "reiniciar", "calculadora", "bloco de notas", "navegador",
    "aumentar volume", "baixar volume", "tela cheia",
    "modo bolinha", "modo minimizado", "minimizar widget", "modo chat",
    "modo hud", "abrir chat", "bate papo", "minimizar whatsapp", "fechar whatsapp",
    "minimizar", "esconder", "ocultar", "apareça", "volte"
]

def execute(query, say, takeCommand, context=None):

    query_lower = query.lower()
    
    # 1. COMANDOS DE MINIMIZAR / ESCONDER
    if any(k in query_lower for k in ["minimizar", "esconder", "ocultar", "bolinha", "se esconda"]):
        # A) Prioridade para Apps Externos (Se o nome do app estiver na frase)
        if any(x in query_lower for x in ["whatsapp", "zap"]):
            windows = gw.getWindowsWithTitle('WhatsApp')
            if windows:
                for win in windows: win.minimize()
                say("WhatsApp minimizado.")
                return True

        if any(x in query_lower for x in ["chrome", "navegador", "edge", "spotify"]):
            pyautogui.hotkey('win', 'down')
            say("Janela minimizada.")
            return True

        # B) Se NÃO mencionou apps externos, a prioridade é a PRÓPRIA LAURA
        # Se falar "Laura", "Widget" ou apenas "Minimizar"
        set_status = context.get("set_status")
        if set_status:
            set_status("idle", "Modo bolinha.", mode="minimized")
            say("Entendido, Olair. Vou ficar em modo bolinha.")
            return True
        return True

    # 2. COMANDOS DE APARECER / VOLTAR
    if any(k in query_lower for k in ["modo hud", "modo normal", "exibir interface", "abrir laura", "apareça", "volte", "voltar", "colte", "vorte", "vorta", "exibir"]):
        set_status = context.get("set_status")
        if set_status: 
            set_status("idle", "Modo normal.", mode="hud")
            say("Estou de volta, Olair.")
            return True

    # 3. FECHAR JANELAS / SAIR DE MODOS
    if any(k in query_lower for k in ["fechar", "encerrar", "parar", "sair"]):
        # Caso especial: Fechar Chat da Laura
        if any(x in query_lower for x in ["chat", "bate papo", "bate-papo", "comms"]):
            set_status = context.get("set_status")
            if set_status: set_status("idle", "Modo normal.", mode="hud")
            say("Fechando bate-papo e voltando ao HUD.")
            return True

        app = query_lower.split("fechar")[-1].strip()
        if "whatsapp" in app or "zap" in app:
            windows = gw.getWindowsWithTitle('WhatsApp')
            if windows:
                for win in windows: win.close()
                say("Encerrando o WhatsApp.")
                return True
        
        # Fallback para outras janelas (Cuidado!)
        if len(query_lower.split()) < 4: # Só faz se for um comando curto como "fechar janela"
            pyautogui.hotkey('alt', 'tab'); time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'w')
            say("Fechando aba ou janela.")
            return True


    # 5. MODOS DE INTERFACE (CHAT)

    if any(k in query_lower for k in ["chat", "bate papo", "bate-papo", "batepapo", "modo chat", "abrir chat", "abrir bate papo", "comms"]):

        set_status = context.get("set_status")
        if set_status: set_status("idle", "Modo Chat.", mode="chat")
        say("Abrindo bate-papo.")
        return True

    return False
