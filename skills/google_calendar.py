import os
import sys
import json
import datetime
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

KEYWORDS = [
    "google calendar", "meu calendar", "calendar", "calendário google",
    "compromissos do google", "agenda do google", "sincronizar agenda",
    "agenda de produção", "calendário de produção", "produção autônoma",
    "agendar no calendar", "criar evento no calendar"
]

# --- PATHS ---
CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")
CLIENT_SECRET_PATH = os.path.join(CREDENTIALS_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, "gcal_token.json")
PRODUCTION_LOG_PATH = os.path.join(BASE_DIR, "production_log.json")

SCOPES = ["https://www.googleapis.com/auth/calendar"]


# =============================================================================
#  AUTENTICAÇÃO OAUTH2
# =============================================================================

def _get_calendar_service():
    """Cria e retorna o serviço autenticado do Google Calendar."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        print("[GoogleCalendar] Bibliotecas do Google não instaladas.")
        print("[GoogleCalendar] Execute: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return None

    creds = None

    # Tenta carregar o token salvo
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception:
            creds = None

    # Se o token expirou, tenta renovar
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None

    # Se não há credenciais válidas, inicia o fluxo OAuth
    if not creds or not creds.valid:
        if not os.path.exists(CLIENT_SECRET_PATH):
            print(f"[GoogleCalendar] Arquivo de credenciais não encontrado em: {CLIENT_SECRET_PATH}")
            print("[GoogleCalendar] Baixe o client_secret.json do Google Cloud Console e coloque na pasta 'credentials/'.")
            return None

        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        # Salva o token para reutilização
        os.makedirs(CREDENTIALS_DIR, exist_ok=True)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
        print("[GoogleCalendar] Token salvo com sucesso.")

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"[GoogleCalendar] Erro ao construir o serviço: {e}")
        return None


# =============================================================================
#  LEITURA DE EVENTOS
# =============================================================================

def list_today_events():
    """Retorna os eventos de hoje do Google Calendar."""
    service = _get_calendar_service()
    if not service:
        return None

    now = datetime.datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return events_result.get("items", [])
    except Exception as e:
        print(f"[GoogleCalendar] Erro ao listar eventos de hoje: {e}")
        return None


def list_week_events():
    """Retorna os eventos da semana do Google Calendar."""
    service = _get_calendar_service()
    if not service:
        return None

    now = datetime.datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_of_week = (now + datetime.timedelta(days=7)).replace(hour=23, minute=59, second=59).isoformat() + "Z"

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_week,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return events_result.get("items", [])
    except Exception as e:
        print(f"[GoogleCalendar] Erro ao listar eventos da semana: {e}")
        return None


# =============================================================================
#  CRIAÇÃO DE EVENTOS
# =============================================================================

def create_event(title, date_str, time_str, duration_minutes=60):
    """Cria um evento no Google Calendar."""
    service = _get_calendar_service()
    if not service:
        return False

    try:
        start_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        event = {
            "summary": title,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "America/Sao_Paulo"
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "America/Sao_Paulo"
            }
        }

        created = service.events().insert(calendarId="primary", body=event).execute()
        print(f"[GoogleCalendar] Evento criado: {created.get('htmlLink')}")
        return True
    except Exception as e:
        print(f"[GoogleCalendar] Erro ao criar evento: {e}")
        return False


# =============================================================================
#  MOTOR DE PRODUÇÃO AUTÔNOMA
# =============================================================================

def _load_production_log():
    """Carrega o log de produções já executadas para evitar duplicação."""
    if not os.path.exists(PRODUCTION_LOG_PATH):
        return []
    try:
        with open(PRODUCTION_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_production_log(log):
    """Salva o log de produções executadas."""
    with open(PRODUCTION_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def check_production_tasks(client, model_to_use, say, takeCommand, skill_manager):
    """
    Verifica o Google Calendar em busca de eventos com prefixos de produção.
    Prefixos reconhecidos:
      [REEL]  → Gera vídeo via trend_hunter + video_explicativo
      [POST]  → Reservado para futuro gerador de carrosséis
      [EBOOK] → Reservado para futuro gerador de e-books
    """
    events = list_today_events()
    if not events:
        return

    production_log = _load_production_log()
    executed_ids = {item["event_id"] for item in production_log}

    production_prefixes = {
        "[REEL]": "video_explicativo",
        "[POST]": "carousel_creator",
        "[EBOOK]": "ebook_creator",
    }

    for event in events:
        event_id = event.get("id", "")
        summary = event.get("summary", "")

        # Verifica se já foi executado
        if event_id in executed_ids:
            continue

        for prefix, target_skill_name in production_prefixes.items():
            if summary.upper().startswith(prefix):
                topic = summary[len(prefix):].strip()

                if not target_skill_name:
                    print(f"[GoogleCalendar] Prefixo '{prefix}' detectado mas skill ainda não implementada. Ignorando: {topic}")
                    continue

                print(f"\n[GoogleCalendar] 🚀 TAREFA DE PRODUÇÃO DETECTADA: {prefix} {topic}")
                say(f"Detectei uma tarefa de produção no Calendar: {prefix} {topic}. Vou iniciar a execução agora.")

                context = {
                    "say": say,
                    "takeCommand": takeCommand,
                    "client": client,
                    "model_to_use": model_to_use,
                    "skill_manager": skill_manager
                }

                try:
                    if target_skill_name == "video_explicativo":
                        # Primeiro, busca tendências sobre o tópico
                        from skills.trend_hunter import fetch_reddit_trends
                        print(f"[GoogleCalendar] Buscando tendências para: {topic}")

                    # Gera o conteúdo (Video, Carrossel ou E-book)
                    target_skill = next(
                        (s for s in skill_manager.skills if s.__name__ == target_skill_name),
                        None
                    )
                    if target_skill:
                        query = f"criar sobre {topic}"
                        target_skill.execute(query, say, takeCommand, context)
                    else:
                        print(f"[GoogleCalendar] Skill '{target_skill_name}' não encontrada.")

                    # Registra como executado
                    production_log.append({
                        "event_id": event_id,
                        "title": summary,
                        "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "completed"
                    })
                    _save_production_log(production_log)
                    print(f"[GoogleCalendar] ✅ Tarefa '{summary}' concluída e registrada no log.")

                except Exception as e:
                    print(f"[GoogleCalendar] ❌ Erro ao executar tarefa '{summary}': {e}")
                    production_log.append({
                        "event_id": event_id,
                        "title": summary,
                        "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": f"error: {e}"
                    })
                    _save_production_log(production_log)

                break  # Só processa um prefixo por evento


# =============================================================================
#  FUNÇÃO PRINCIPAL (SKILL EXECUTE)
# =============================================================================

def _format_event_time(event):
    """Formata o horário de um evento para exibição."""
    start = event.get("start", {})
    if "dateTime" in start:
        dt = datetime.datetime.fromisoformat(start["dateTime"])
        return dt.strftime("%H:%M")
    return "dia inteiro"


def execute(query, say, takeCommand, context=None):
    """Ponto de entrada da skill. Chamado pelo SkillManager."""
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    query_lower = query.lower()

    # --- VERIFICAR CALENDÁRIO DO GOOGLE ---
    service = _get_calendar_service()
    if not service:
        say("Senhor, o Google Calendar ainda não está configurado. "
            "Preciso que você coloque o arquivo client_secret.json na pasta credentials do projeto. "
            "Posso te guiar no processo se quiser.")
        return True

    # --- LISTAR EVENTOS DE HOJE ---
    if any(w in query_lower for w in ["hoje", "compromissos", "agenda", "meu dia", "calendar"]):
        if "semana" in query_lower or "próximos" in query_lower:
            say("Consultando seus eventos da semana no Google Calendar...")
            events = list_week_events()
            label = "esta semana"
        else:
            say("Consultando seus eventos de hoje no Google Calendar...")
            events = list_today_events()
            label = "hoje"

        if not events:
            say(f"Você não tem compromissos para {label} no Google Calendar.")
        else:
            say(f"Encontrei {len(events)} eventos para {label}:")
            for event in events:
                time_str = _format_event_time(event)
                title = event.get("summary", "Sem título")
                say(f"Às {time_str}, {title}.")

            # Verifica se há tarefas de produção pendentes
            production_events = [e for e in events if any(
                e.get("summary", "").upper().startswith(p) for p in ["[REEL]", "[POST]", "[EBOOK]"]
            )]
            if production_events:
                say(f"Identifiquei {len(production_events)} tarefas de produção automática. "
                    f"Elas serão executadas no horário agendado.")

        return True

    # --- CRIAR EVENTO NO CALENDAR ---
    if any(w in query_lower for w in ["agendar", "criar evento", "marcar", "adicionar"]):
        say("Entendido. Vou processar os detalhes do evento para o Google Calendar.")

        if not client or not model:
            say("Não consigo processar sem o motor de IA ativo.")
            return True

        today = datetime.datetime.now().strftime("%Y-%m-%d (%A)")
        prompt = f"""
        Extraia os dados de um evento de calendário da frase do usuário.
        Hoje é {today}. Responda APENAS um JSON:
        {{"title": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "duration": 60}}
        
        Frase: "{query}"
        """

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um extrator de JSON preciso."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            content = response.choices[0].message.content.strip()
            if "{" in content:
                content = content[content.find("{"):content.rfind("}") + 1]
            info = json.loads(content)

            success = create_event(
                title=info.get("title", "Evento Laura"),
                date_str=info.get("date"),
                time_str=info.get("time", "09:00"),
                duration_minutes=info.get("duration", 60)
            )

            if success:
                say(f"Evento criado no Google Calendar: {info['title']} para {info['date']} às {info['time']}. "
                    f"Ele já vai aparecer no seu celular.")
            else:
                say("Não consegui criar o evento. Verifique se a autenticação está correta.")

        except Exception as e:
            say("Tive um problema ao processar o evento.")
            print(f"[GoogleCalendar] Erro na criação via IA: {e}")

        return True

    # --- VERIFICAR PRODUÇÃO PENDENTE ---
    if any(w in query_lower for w in ["produção", "tarefas automáticas", "verificar calendar"]):
        say("Verificando tarefas de produção autônoma no Calendar...")
        skill_manager = context.get("skill_manager")
        check_production_tasks(client, model, say, takeCommand, skill_manager)
        say("Verificação de produção concluída.")
        return True

    # Fallback: lista os eventos de hoje
    say("Consultando o Google Calendar...")
    events = list_today_events()
    if events:
        say(f"Você tem {len(events)} eventos hoje:")
        for event in events:
            time_str = _format_event_time(event)
            title = event.get("summary", "Sem título")
            say(f"Às {time_str}, {title}.")
    else:
        say("Sua agenda do Google Calendar está livre hoje.")

    return True
