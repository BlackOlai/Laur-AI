"""
Heartbeat da Laura — inspirado no módulo `heartbeat/` do Conway-Research/automaton.

Daemon que roda em background e dá "vida autônoma" à Laura:
1. Executa tarefas agendadas vencidas (scheduled_tasks.json) — hoje gravadas
   pela skill task_scheduler mas nunca consumidas.
2. Suporta lembretes (type=reminder) anunciados por voz.
3. Registra tudo em heartbeat_log.json (audit log, conceito do self-mod/).

Uso (em Laura.py -> main_loop):
    from core.heartbeat import start_heartbeat
    start_heartbeat(say)
"""

import os
import json
import time
import datetime
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_FILE = os.path.join(BASE_DIR, "scheduled_tasks.json")
LOG_FILE = os.path.join(BASE_DIR, "heartbeat_log.json")

# Intervalo de varredura (segundos) — configurável via .env
INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))

_tasks_lock = threading.Lock()

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_tasks(tasks):
    with _tasks_lock:
        try:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Heartbeat] Erro ao salvar tarefas: {e}")

def _log_event(event, detail=""):
    """Audit log simples — todos os batimentos relevantes ficam registrados."""
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        logs.append({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "detail": detail,
        })
        logs = logs[-200:]  # mantém no máximo os últimos 200 eventos
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Heartbeat] Erro no audit log: {e}")

# ---------------------------------------------------------------------------
# Lógica de vencimento
# ---------------------------------------------------------------------------

def _is_due(task, now):
    """Verifica se a tarefa venceu (data+hora <= agora) e está pendente."""
    if task.get("status") != "pending":
        return False
    try:
        t_date = task.get("date", "")
        t_time = task.get("time", "00:00")
        if not t_date:
            return False
        due = datetime.datetime.strptime(f"{t_date} {t_time}", "%Y-%m-%d %H:%M")
        # Janela de execução: venceu há menos de 1 hora (evita disparar
        # tarefas muito antigas acumuladas de sessões passadas)
        return due <= now <= due + datetime.timedelta(hours=1)
    except Exception:
        return False

def _mark_task(task_id, status, detail=""):
    tasks = load_tasks()
    for t in tasks:
        if (t.get("id") or f"{t.get('date')}_{t.get('time')}_{t.get('contact')}") == task_id:
            t["status"] = status
            if detail:
                t["result"] = detail
            break
    save_tasks(tasks)

# ---------------------------------------------------------------------------
# Executores por tipo de tarefa
# ---------------------------------------------------------------------------

def _execute_whatsapp(task, say):
    """Envia WhatsApp via automação do desktop (sem interação de voz)."""
    contact = task.get("contact", "")
    message = task.get("message", "")
    if not contact or not message:
        return "contato ou mensagem vazios"
    try:
        from skills.whatsapp_sender import send_whatsapp_desktop
        # takeCommand dummy: a automação não deve pedir input no heartbeat
        def _no_input(*a, **k):
            return "none"
        ok = send_whatsapp_desktop(contact, message, say, _no_input)
        return "enviado" if ok else "falha no envio"
    except Exception as e:
        return f"erro: {e}"

def _execute_reminder(task, say):
    say(f"Lembrete, senhor: {task.get('message', '')}")
    return "lembrado"

def _execute_announce(task, say):
    say(str(task.get("message", "")))
    return "anunciado"

def _execute_job(task, say):
    """
    Job composto: dispara o agente autônomo para produzir de verdade
    (tendências → copy → carrossel/vídeo...) sem interação de voz.
    Requer get_context injetado no start_heartbeat (Laura.py fornece).
    """
    getter = _EXEC_STATE.get("get_context")
    if not getter:
        return "sem contexto (heartbeat iniciado sem get_context)"
    try:
        ctx = getter()
        if not ctx or not ctx.get("client"):
            return "contexto de IA indisponível"
        ctx["auto_confirm"] = True  # executa sem pedir confirmação por voz
        from skills.autonomous_agent import execute as run_agent
        objetivo = str(task.get("message", "") or task.get("job", "produzir conteúdo"))
        run_agent(objetivo, say, lambda *a, **k: "none", ctx)
        return "job executado pelo agente autônomo"
    except Exception as e:
        return f"erro: {e}"

EXECUTORS = {
    "whatsapp": _execute_whatsapp,
    "reminder": _execute_reminder,
    "announce": _execute_announce,
    "job": _execute_job,
}

# Estado interno compartilhado entre start_heartbeat e executores
_EXEC_STATE = {"get_context": None}

# ---------------------------------------------------------------------------
# Ponte com a HUD (widget.html) — feed de atividade + progresso de job
# ---------------------------------------------------------------------------

_WIDGET_DATA_FILE = os.path.join(BASE_DIR, "widget_data.json")

def push_activity(text):
    """Registra um evento no feed de atividade autônoma (lido pela HUD)."""
    import json as _json
    data = {}
    try:
        if os.path.exists(_WIDGET_DATA_FILE):
            with open(_WIDGET_DATA_FILE, "r", encoding="utf-8") as f:
                data = _json.load(f)
    except Exception:
        data = {}
    feed = data.get("activity", [])
    feed.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M"),
        "text": str(text)[:120],
    })
    data["activity"] = feed[:8]
    try:
        with open(_WIDGET_DATA_FILE, "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Heartbeat] Erro ao publicar atividade: {e}")

def set_job_progress(current, total, label=""):
    """Publica o progresso do job corrente no status.json (anel da HUD)."""
    try:
        from core.status import set_status as _set
        _set("working", label or "Executando job...",
             job={"current": current, "total": total, "label": str(label)[:80]})
    except Exception as e:
        print(f"[Heartbeat] Erro ao publicar progresso: {e}")

def clear_job_progress(summary=""):
    try:
        from core.status import set_status as _set
        _set("idle", "", job=None)
    except Exception as e:
        print(f"[Heartbeat] Erro ao limpar progresso do job: {e}")

# ---------------------------------------------------------------------------
# Ciclo principal
# ---------------------------------------------------------------------------

def beat(say, context=None):
    """Um batimento: procura e executa tarefas vencidas. Retorna qtd executada."""
    now = datetime.datetime.now()
    tasks = load_tasks()
    executed = 0

    for task in tasks:
        if not _is_due(task, now):
            continue

        task_id = task.get("id") or f"{task.get('date')}_{task.get('time')}_{task.get('contact')}"
        ttype = (task.get("type") or "announce").lower()
        executor = EXECUTORS.get(ttype, _execute_announce)

        print(f"[Heartbeat] Executando tarefa vencida ({ttype}): {task.get('contact', '')} -> {str(task.get('message', ''))[:50]}")
        _log_event("task_started", f"{ttype}: {str(task.get('message', ''))[:80]}")

        try:
            result = executor(task, say)
        except Exception as e:
            result = f"erro: {e}"

        _mark_task(task_id, "done", result)
        _log_event("task_done", f"{ttype}: {result}")
        push_activity(f"{ttype.upper()} -> {result} ({str(task.get('message', ''))[:40]})")
        executed += 1

    return executed

def start_heartbeat(say, interval=None, get_context=None):
    """Inicia o daemon do heartbeat em thread separada (daemon=True).

    get_context: função opcional que retorna o contexto completo da Laura
    (client, model_to_use, skill_manager...). Necessário para jobs compostos.
    """
    if interval is None:
        interval = INTERVAL
    _EXEC_STATE["get_context"] = get_context

    def loop():
        print(f"[Heartbeat] Ativo. Varredura a cada {interval}s.")
        _log_event("heartbeat_started", f"intervalo={interval}s")
        beat_count = 0
        while True:
            try:
                beat(say)
            except Exception as e:
                print(f"[Heartbeat Error] {e}")
                _log_event("heartbeat_error", str(e))

            # Fase 5: detecção de padrões de evolução a cada 10 batimentos
            beat_count += 1
            if beat_count % 10 == 0:
                try:
                    from core.pattern_detector import run_detection
                    run_detection(push_activity=push_activity)
                except Exception as e:
                    print(f"[PatternDetector Error] {e}")

            time.sleep(interval)

    threading.Thread(target=loop, daemon=True).start()
