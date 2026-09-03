import json
import os
import datetime

KEYWORDS = ["agendar whatsapp", "mande um zap às", "enviar mensagem às", "mandar zap mais tarde", "agende um whatsapp", "o que tem agendado", "ver agendamentos", "lista de tarefas", "cancelar agendamento", "remover agendamento", "cancelar whatsapp"]

# Caminho absoluto baseado na raiz do projeto (um nível acima da pasta skills)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_FILE = os.path.join(BASE_DIR, "scheduled_tasks.json")

def load_tasks():
    if not os.path.exists(TASKS_FILE): return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except: pass

def extract_schedule_info(query, context):
    client = context.get("client")
    model = context.get("model_to_use")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    Extraia dados de agendamento de: "{query}"
    Hoje é {today}. O horário atual aproximado é {datetime.datetime.now().strftime("%H:%M")}.
    
    IMPORTANTE: 
    1. Se o usuário disser um horário como "8 e 10" e já passar das 8 da manhã, assuma que é 20:10 (noite).
    2. Use SEMPRE o formato 24h (00:00 até 23:59).
    
    Responda APENAS JSON:
    {{
      "contact": "...",
      "message": "...",
      "time": "HH:MM",
      "date": "YYYY-MM-DD"
    }}
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        if "{" in content:
            content = content[content.find("{"):content.rfind("}")+1]
        return json.loads(content)
    except: return None

def execute(query, say, takeCommand, context=None):
    query = query.lower()
    
    # 1. LISTAR TAREFAS
    if any(w in query for w in ["o que tem agendado", "ver agendamentos", "lista"]):
        tasks = load_tasks()
        pending = [t for t in tasks if t.get("status") == "pending"]
        if not pending:
            say("Não há tarefas pendentes na fila, senhor.")
        else:
            say(f"Senhor, você tem {len(pending)} tarefas agendadas:")
            for t in pending:
                say(f"Mensagem para {t['contact']} às {t['time']}.")
        return True

    # 2. CANCELAR TAREFAS
    if any(w in query for w in ["cancelar", "remover", "excluir"]) and any(w in query for w in ["agendamento", "whatsapp", "zap", "tarefa"]):
        tasks = load_tasks()
        pending = [t for t in tasks if t.get("status") == "pending"]
        
        if not pending:
            say("Não encontrei nenhum agendamento pendente para cancelar, senhor.")
            return True
            
        if len(pending) == 1:
            task = pending[0]
            say(f"Encontrei um agendamento para {task['contact']} às {task['time']}. Deseja cancelar?")
            confirm = takeCommand().lower()
            if any(w in confirm for w in ["sim", "pode", "quero", "cancela"]):
                tasks.remove(task)
                save_tasks(tasks)
                say("Agendamento cancelado com sucesso.")
            else:
                say("Tudo bem, mantive o agendamento.")
        else:
            say("Qual agendamento o senhor deseja cancelar? Diga o nome do contato.")
            contact_to_cancel = takeCommand().lower()
            if contact_to_cancel == "none": return True
            
            # Procura a tarefa pelo nome do contato
            to_remove = [t for t in pending if contact_to_cancel in t['contact'].lower()]
            if to_remove:
                if len(to_remove) > 1:
                    say(f"Encontrei {len(to_remove)} agendamentos para {contact_to_cancel}. Qual o horário do que deseja remover?")
                    time_choice = takeCommand()
                    to_remove = [t for t in to_remove if time_choice in t['time']]
                
                if to_remove:
                    for item in to_remove:
                        tasks.remove(item)
                    save_tasks(tasks)
                    say(f"Agendamento para {contact_to_cancel} removido.")
                else:
                    say("Não consegui identificar o horário exato, cancelamento abortado.")
            else:
                say(f"Não encontrei agendamentos pendentes para {contact_to_cancel}.")
        return True

    # 3. AGENDAR NOVA TAREFA
    say("Agendando. Só um segundo...")
    info = extract_schedule_info(query, context)
    if not info: info = {"contact": "", "message": "", "time": "", "date": ""}

    if not info.get("contact"):
        say("Com certeza, senhor. Para quem devo enviar essa mensagem?")
        info["contact"] = takeCommand()
        if info["contact"] == "none": return True

    if not info.get("message"):
        say(f"Entendido. E o que o senhor gostaria de dizer para {info['contact']}?")
        info["message"] = takeCommand()
        if info["message"] == "none": return True

    if not info.get("time"):
        say("Perfeito. Só me confirme o horário em que devo realizar o envio.")
        time_query = takeCommand()
        import re
        match = re.search(r"(\d{1,2})[:h\s]*(\d{0,2})", time_query)
        if match:
            h = match.group(1).zfill(2)
            m = match.group(2).zfill(2) if match.group(2) else "00"
            info["time"] = f"{h}:{m}"
        else:
            say("Não entendi o horário.")
            return True

    if not info.get("date"):
        info["date"] = datetime.datetime.now().strftime("%Y-%m-%d")

    tasks = load_tasks()
    info["status"] = "pending"
    info["type"] = "whatsapp"
    tasks.append(info)
    save_tasks(tasks)
    
    say(f"Perfeito senhor. Agendado para {info['contact']} às {info['time']}.")
    return True
