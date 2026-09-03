import json
import os
import datetime
import re

KEYWORDS = ["marcar compromisso", "agendar", "agenda de hoje", "meus compromissos", "limpar agenda", "remover compromisso", "o que eu tenho"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENDA_FILE = os.path.join(BASE_DIR, "agenda.json")


def load_agenda():
    if not os.path.exists(AGENDA_FILE):
        return []
    try:
        with open(AGENDA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_agenda(agenda):
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, ensure_ascii=False, indent=2)

def extract_event_info(query, context):
    """Usa a IA para extrair título, data e hora da frase."""
    client = context.get("client")
    model = context.get("model_to_use")

    today = datetime.datetime.now().strftime("%Y-%m-%d (%A)")
    
    prompt = f"""
    Você é um extrator de dados para uma agenda. 
    Analise a frase do usuário e extraia:
    1. Título do compromisso.
    2. Data no formato YYYY-MM-DD. (Hoje é {today}).
    3. Hora no formato HH:MM (se não houver, use "00:00").
    
    Frase: "{query}"
    
    Responda EXCLUSIVAMENTE um objeto JSON como este:
    {{"title": "...", "date": "YYYY-MM-DD", "time": "HH:MM"}}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Você é um extrator de JSON preciso."}, {"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Erro na extração IA: {e}")
        return None

def generate_strategic_insight(say, context, agenda_events):
    """Gera um insight estratégico baseado na agenda atual."""
    client = context.get("client")
    model = context.get("model_to_use")
    
    if not client or not model: return

    prompt = f"""
    Você é a Laura, consultora estratégica.
    Agenda de Hoje: {json.dumps(agenda_events, ensure_ascii=False)}
    
    Dê um INSIGHT ESTRATÉGICO curto (máximo 2 frases) sobre o dia do usuário.
    Se a agenda estiver vazia, foque em planejamento ou prospecção.
    Se estiver cheia, foque em priorização.
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Você é Laura, elegante e estratégica."}, {"role": "user", "content": prompt}]
        )
        insight = response.choices[0].message.content.strip()
        say(f"Insight do dia: {insight}")
    except:
        pass

def execute(query, say, takeCommand, context=None):
    query = query.lower()
    agenda = load_agenda()

    # --- ADICIONAR COMPROMISSO ---
    if "marcar" in query or "agendar" in query:
        say("Entendido senhor, estou processando os detalhes do compromisso.")
        info = extract_event_info(query, context)
        
        if info and info.get("title") and info.get("date"):
            new_event = {
                "id": len(agenda) + 1,
                "title": info["title"],
                "date": info["date"],
                "time": info["time"],
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            agenda.append(new_event)
            save_agenda(agenda)
            say(f"Perfeito senhor! Agendei {info['title']} para o dia {info['date']} às {info['time']}.")
        else:
            say("Não consegui entender bem a data ou o título. Poderia repetir com mais detalhes?")

    # --- LISTAR COMPROMISSOS ---
    elif any(w in query for w in ["agenda", "compromissos", "tenho", "meu dia", "minha agenda"]):
        target_date = datetime.datetime.now().strftime("%Y-%m-%d")
        day_label = "hoje"
        
        if "amanhã" in query:
            target_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            day_label = "amanhã"
        
        events = [e for e in agenda if e["date"] == target_date]
        
        if not events:
            say(f"Senhor, você não tem compromissos marcados para {day_label}.")
        else:
            say(f"Para {day_label}, você tem os seguintes compromissos:")
            for e in sorted(events, key=lambda x: x["time"]):
                say(f"Às {e['time']}, {e['title']}.")
        
        # Gera o insight estratégico APENAS quando solicitado a agenda
        generate_strategic_insight(say, context, events)

    # --- LIMPAR / REMOVER ---
    elif "limpar" in query or "esvaziar" in query:
        say("Tem certeza que deseja apagar todos os compromissos da agenda?")
        confirm = takeCommand().lower()
        if "sim" in confirm or "pode" in confirm:
            save_agenda([])
            say("Agenda limpa com sucesso, senhor.")
        else:
            say("Entendido, mantive seus compromissos.")

    return True
