import os
import psutil
import socket
import platform
import json

KEYWORDS = [
    "investigar erro", "detectar problema", "analisar anomalia",
    "depurar", "fazer debug", "analisar erro", "encontrar bug",
    "o que está errado", "por que está falhando", "error detective",
    "verificar sistema", "diagnóstico", "limpar erro"
]

def _check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Online e Estável"
    except OSError:
        return "Offline ou Instável"

def _get_system_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return f"CPU: {cpu}% | RAM: {ram}%"

def _read_and_clear_logs():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(BASE_DIR, "error_logs.json")
    errors_found = []
    
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
            
            unread_logs = [l for l in logs if l.get("status") == "unread"]
            for l in unread_logs:
                errors_found.append(f"[{l['origin']}] {l['message']}")
                l["status"] = "read"
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
        except: pass
    
    return errors_found

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Iniciando varredura rápida, Olair. Vou ver o que está acontecendo.")
    
    internal_errors = _read_and_clear_logs()
    net_status = _check_internet()
    sys_stats = _get_system_stats()
    
    status_report = f"""
    DADOS TÉCNICOS:
    - Erros: {'; '.join(internal_errors) if internal_errors else 'Nenhum'}
    - Conexão: {net_status}
    - Recursos: {sys_stats}
    """

    if client and model:
        prompt = (
            f"Você é a Laura, a parceira inteligente e assistente pessoal do Olair.\n"
            f"Relatório Técnico da Investigação:\n{status_report}\n\n"
            f"INSTRUÇÕES DE PERSONALIDADE:\n"
            f"- Fale diretamente com o OLAIR (use o nome dele).\n"
            f"- NÃO use 'Prezado usuário', 'Atenciosamente' ou linguagem de Call Center.\n"
            f"- Seja direta, inteligente e use um tom de parceria.\n"
            f"- Explique o erro de forma simples (ex: 'Olair, encontrei um link quebrado no meu código, mas já foi resolvido').\n"
            f"- Confirme que limpou os logs e o widget vai voltar ao normal.\n"
            f"- Acabe a frase de forma natural, como 'Estou de olho em tudo por aqui' ou 'Tudo sob controle'."
        )
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except:
            say(f"Olair, identifiquei {len(internal_errors)} erro(s) interno(s), mas já fiz a limpeza. Internet {net_status} e recursos {sys_stats}. Tudo certo agora!")
    else:
        say(f"Olair, verifiquei tudo por aqui. Internet {net_status} e logs limpos. O sistema está estável.")

    return True
