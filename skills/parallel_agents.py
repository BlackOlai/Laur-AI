import threading
import time

KEYWORDS = [
    "em paralelo", "ao mesmo tempo", "simultaneamente", "paralelo",
    "todas as informações", "tudo de uma vez", "resumo completo",
    "checar tudo", "verificar tudo", "briefing completo", "painel de status"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    skill_manager = context.get("skill_manager") if context else None

    say("Ativando agentes paralelos. Disparando múltiplas consultas simultaneamente...")

    results = {}
    errors = []
    lock = threading.Lock()

    def fetch_weather():
        try:
            import json, os
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file = os.path.join(BASE_DIR, "widget_data.json")
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                w = data.get("weather", {})
                if w:
                    with lock:
                        results["clima"] = f"{w.get('city','').split(',')[0]}: {round(w.get('temp',0))}°C, {w.get('condition','')}"
                    return
            with lock:
                results["clima"] = "Dado de clima não disponível no cache."
        except Exception as e:
            with lock:
                errors.append(f"Clima: {e}")

    def fetch_news():
        try:
            import json, os
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file = os.path.join(BASE_DIR, "widget_data.json")
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                news = data.get("news_ia", {})
                if news:
                    with lock:
                        results["notícias"] = news.get("title", "Sem notícias no cache.")
                    return
            with lock:
                results["notícias"] = "Cache de notícias não disponível."
        except Exception as e:
            with lock:
                errors.append(f"Notícias: {e}")

    def fetch_market():
        try:
            import json, os
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file = os.path.join(BASE_DIR, "widget_data.json")
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cot = data.get("cotacao", {})
                if cot:
                    with lock:
                        results["mercado"] = f"Dólar: R${float(cot.get('dolar',0)):.2f} | Euro: R${float(cot.get('euro',0)):.2f}"
                    return
            with lock:
                results["mercado"] = "Cotações não disponíveis."
        except Exception as e:
            with lock:
                errors.append(f"Mercado: {e}")

    def fetch_agenda():
        try:
            import json, os, datetime
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            agenda_file = os.path.join(BASE_DIR, "agenda.json")
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            if os.path.exists(agenda_file):
                with open(agenda_file, "r", encoding="utf-8") as f:
                    agenda = json.load(f)
                today_events = [e for e in agenda if e.get("date") == today]
                if today_events:
                    titles = ", ".join([e.get("title","") for e in today_events[:3]])
                    with lock:
                        results["agenda"] = f"{len(today_events)} compromisso(s): {titles}"
                else:
                    with lock:
                        results["agenda"] = "Nenhum compromisso hoje."
            else:
                with lock:
                    results["agenda"] = "Agenda vazia."
        except Exception as e:
            with lock:
                errors.append(f"Agenda: {e}")

    # Disparar todos os agentes em paralelo
    agents = [
        threading.Thread(target=fetch_weather, daemon=True),
        threading.Thread(target=fetch_news, daemon=True),
        threading.Thread(target=fetch_market, daemon=True),
        threading.Thread(target=fetch_agenda, daemon=True),
    ]
    for a in agents:
        a.start()
    for a in agents:
        a.join(timeout=5)  # Aguarda no máximo 5 segundos por agente

    # Montar relatório consolidado
    report_parts = ["Senhor, aqui está seu painel de status completo:"]
    label_map = {"clima": "🌤 Clima", "notícias": "📰 IA & Tecnologia", "mercado": "💹 Mercado", "agenda": "📅 Agenda"}
    for key, label in label_map.items():
        if key in results:
            report_parts.append(f"{label}: {results[key]}")

    say(". ".join(report_parts))
    return True
