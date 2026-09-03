import os
import time
import pyautogui
import pygetwindow as gw

KEYWORDS = ["mandar whatsapp", "enviar whatsapp", "mensagem no whatsapp", "whatsapp para"]

def send_whatsapp_desktop(contact, message, say, takeCommand):
    """Automação nativa para o App Desktop do WhatsApp."""
    say(f"Localizando o WhatsApp Desktop para enviar para {contact}...")
    
    # 1. Tenta encontrar a janela do WhatsApp
    windows = gw.getWindowsWithTitle('WhatsApp')
    if not windows:
        say("Senhor, o aplicativo do WhatsApp não parece estar aberto no seu computador.")
        say("Deseja que eu tente pelo navegador ou prefere abrir o App?")
        ans = takeCommand(timeout=10).lower()
        if any(w in ans for w in ["sim", "pode", "navegador", "web"]):
            import webbrowser
            import urllib.parse
            # Fallback para Web
            phone = ''.join(filter(str.isdigit, contact))
            if len(phone) < 10:
                say("Para o navegador, preciso do número com DDD. Qual o número?")
                phone = ''.join(filter(str.isdigit, takeCommand(timeout=15)))
            
            if len(phone) >= 10:
                if not phone.startswith("55"): phone = "55" + phone
                say("Abrindo WhatsApp Web...")
                webbrowser.open(f"https://web.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(message)}")
                return True
        return False

    # 2. Ativa o App
    win = windows[0]
    try:
        if win.isMinimized: win.restore()
        win.activate()
        time.sleep(1.5) # Tempo para o Windows focar a janela
    except:
        say("Não consegui trazer a janela do WhatsApp para o primeiro plano.")
        return False

    # 3. Fluxo de busca e envio (Simulação humana)
    try:
        # Atalho padrão do WhatsApp Desktop para busca (Ctrl + F)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        
        # Limpa busca anterior e digita contato
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(contact, interval=0.1)
        time.sleep(2.0) # Espera o App filtrar os contatos
        pyautogui.press('enter')
        time.sleep(1.0)
        
        # Digita e envia a mensagem
        pyautogui.write(message, interval=0.05)
        pyautogui.press('enter')
        return True
    except Exception as e:
        print(f"[WhatsApp Error] {e}")
        return False

def execute(query, say, takeCommand, context=None):
    query_lower = query.lower()
    
    # Tenta descobrir o destinatário na própria frase
    destinatario = ""
    if "para " in query_lower:
        destinatario = query_lower.split("para ")[-1].strip()
    
    if not destinatario:
        say("Para quem devo enviar o WhatsApp?")
        destinatario = takeCommand(timeout=10)
        
    if not destinatario or destinatario == "none": 
        say("Envio cancelado.")
        return True
        
    say(f"O que deseja dizer para {destinatario}?")
    texto = takeCommand(timeout=25)
    
    if not texto or texto == "none":
        say("Entendido, não enviarei nada.")
        return True
        
    if send_whatsapp_desktop(destinatario, texto, say, takeCommand):
        say("Mensagem enviada com sucesso pelo aplicativo.")
    else:
        say("Não consegui concluir o envio pelo aplicativo.")
    
    return True
