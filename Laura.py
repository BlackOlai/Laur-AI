"""Laura \u2014 n\u00facleo de la asistente (refactor prompt 09).

Este m\u00f3dulo es el orquestador: configura el motor de IA, instancia los
managers y mantiene el bucle principal (voz/chat). Las responsabilidades
extra\u00edbles viven en core/ (chat_engine, background, system_log,
chat_persistence).

Interfaz p\u00fablica preservada: main_loop, validate_config, chat,
background_tasks, log_system_error \u2014 los launchers importan igual.
"""
import os
import time
import datetime
import threading
import random
from dotenv import load_dotenv
from openai import OpenAI

from core.stt import takeCommand
from core.tts import say
from core.status import set_status
from core.skill_manager import SkillManager
from core.config_manager import validate_config
from core.memory_manager import MemoryManager
from core.mcp_manager import MCPManager

# M\u00f3dulos extra\u00eddos en el refactor \u2014 se re-exportan para preservar la interfaz.
from core.system_log import log_system_error  # noqa: F401
from core.chat_persistence import persist_chat_history as _persist_chat_history
from core.chat_engine import chat as _chat_engine
from core.background import background_tasks as _background_tasks

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def get_ai_client():
    """Cliente y modelo seg\u00fan prioridad: Groq > NVIDIA > OpenRouter."""
    if GROQ_API_KEY:
        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY), "llama-3.3-70b-versatile"
    elif NVIDIA_API_KEY:
        return OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY), "minimaxai/minimax-m2.7"
    else:
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY), "google/gemini-2.0-pro-exp-02-05:free"


client, model_to_use = get_ai_client()
skill_manager = SkillManager()

try:
    memory_manager = MemoryManager()
except Exception as e:
    print(f"[Warning] Falha ao inicializar o banco de mem\u00f3rias: {e}")
    memory_manager = None

try:
    mcp_manager = MCPManager()
except Exception as e:
    print(f"[Warning] Falha ao inicializar o MCP Manager: {e}")
    mcp_manager = None

MAX_HISTORY_MESSAGES = int(os.getenv("LAURA_MAX_HISTORY", "40"))
conversation_history = []
CONTINUOUS_WINDOW = float(os.getenv("LAURA_CONTINUOUS_WINDOW", "30"))


def _chat_deps():
    """Dependencias vivas para el motor de chat (core/chat_engine)."""
    return {
        "client": client, "model_to_use": model_to_use,
        "memory_manager": memory_manager, "mcp_manager": mcp_manager,
        "set_status": set_status, "say": say,
        "log_system_error": log_system_error,
        "persist_chat_history": _persist_chat_history,
    }


def chat(query):
    """Chat de IA general con memoria de sesi\u00f3n (delega en core/chat_engine)."""
    _chat_engine(query, _chat_deps(), conversation_history, MAX_HISTORY_MESSAGES)


def background_tasks():
    """Tareas de segundo plano (delega en core/background)."""
    _background_tasks(client, model_to_use, say, takeCommand, skill_manager)


def build_laura_context():
    """Contexto completo para ejecuci\u00f3n aut\u00f3noma (heartbeat/jobs)."""
    return {
        "say": say, "takeCommand": takeCommand, "set_status": set_status,
        "log_system_error": log_system_error, "client": client,
        "model_to_use": model_to_use, "skill_manager": skill_manager,
        "memory_manager": memory_manager,
    }
def main_loop():
    threading.Thread(target=background_tasks, daemon=True).start()

    try:
        from core.heartbeat import start_heartbeat
        start_heartbeat(say, get_context=build_laura_context)
    except Exception as e:
        print(f"[Warning] Falha ao iniciar o heartbeat: {e}")

    hora = datetime.datetime.now().hour
    saudacoes_bomdia = ["Bom dia, Olair!", "Olá Olair, bom dia! Pronta para ajudar."]
    saudacoes_boatarde = ["Boa tarde, Olair! Como posso ser útil?", "Boa tarde, senhor! Em que trabalhamos agora?"]
    saudacoes_boanoite = ["Boa noite, Olair!", "Boa noite, senhor! No que posso ajudar?"]

    if 5 <= hora < 12:
        msg = random.choice(saudacoes_bomdia)
    elif 12 <= hora < 18:
        msg = random.choice(saudacoes_boatarde)
    else:
        msg = random.choice(saudacoes_boanoite)

    time.sleep(2)
    say(msg)

    continuous_mode = False
    last_interaction_time = 0
    context = build_laura_context()  # contexto do main_loop (usado nas skills/router)

    while True:
        try:
            if continuous_mode and (time.time() - last_interaction_time < CONTINUOUS_WINDOW):
                raw_query, source = takeCommand(timeout=3, return_source=True)
                if not raw_query or raw_query == "none":
                    continuous_mode = False
                    set_status("idle", "")
                    continue
                if source == "widget" or "http" in raw_query:
                    query = raw_query.replace("laura", "").strip()
                elif "laura" in raw_query:
                    query = raw_query.replace("laura", "").strip()
                    if not query:
                        say("Sim, Olair?")
                        raw_query2, _ = takeCommand(timeout=5, return_source=True)
                        query = raw_query2
                else:
                    query = raw_query
            else:
                continuous_mode = False
                set_status("idle", "")
                raw_query, source = takeCommand(timeout=None, return_source=True)

                if not raw_query or raw_query == "none":
                    continue

                if source == "widget" or "http" in raw_query:
                    query = raw_query.replace("laura", "").strip()
                elif "laura" in raw_query:
                    query = raw_query.replace("laura", "").strip()
                    if not query:
                        say("Sim, Olair?")
                        raw_query2, _ = takeCommand(timeout=5, return_source=True)
                        query = raw_query2
                else:
                    continue

            if not query or query == "none":
                continue

            if query.strip() == "__MIC_TRIGGER__":
                say("Estou ouvindo, senhor.")
                continuous_mode = True
                last_interaction_time = time.time()
                continue

            if any(cmd in query for cmd in ["parar", "silêncio", "pare", "cancelar"]):
                say("Certo.")
                continuous_mode = False
                continue

            if any(cmd in query for cmd in ["limpar memória", "esquecer conversa", "nova conversa", "resetar contexto"]):
                conversation_history.clear()
                say("Memória de sessão limpa. Começando do zero, Olair.")
                continuous_mode = False
                continue

            # 1. Match directo de keywords (habilidades del sistema)
            if skill_manager.handle(query, say, takeCommand, context):
                continuous_mode = True
                last_interaction_time = time.time()
                continue

            # Refuerzo: si es un link y el SkillManager falló, fuerza análisis
            if "http" in query.lower():
                try:
                    from skills.link_analyzer import execute as link_exec
                    if link_exec(query, say, takeCommand, context):
                        continuous_mode = True
                        last_interaction_time = time.time()
                        continue
                except Exception as e:
                    print(f"[REFORÇO] Falha ao forzar link_analyzer: {e}")

            # 2. Roteador estratégico (IA decide la skill); recibe matches débiles
            from skills.skill_router import execute as route_intent
            routed = route_intent(query, say, takeCommand, context)
            if routed:
                continuous_mode = True
                last_interaction_time = time.time()
            else:
                weak_skill = context.pop("weak_skill_match", None) if context else None
                if weak_skill is not None:
                    try:
                        print(f"[MainLoop] Router no resolvió — skill pospuesta: {weak_skill.__name__}")
                        res = weak_skill.execute(query, say, takeCommand, context)
                        if res is not False:
                            try:
                                from core.skill_protocol import normalize
                                context["last_skill_result"] = normalize(res, weak_skill.__name__)
                            except Exception:
                                pass
                            continuous_mode = True
                            last_interaction_time = time.time()
                        else:
                            chat(query)
                            continuous_mode = True
                            last_interaction_time = time.time()
                    except Exception as e:
                        log_system_error("Weak Skill Fallback", e)
                        chat(query)
                        continuous_mode = True
                        last_interaction_time = time.time()
                else:
                    # 3. Chat de inteligencia general
                    chat(query)
                    continuous_mode = True
                    last_interaction_time = time.time()

        except Exception as e:
            log_system_error("Main Loop", e)
            time.sleep(1)


if __name__ == "__main__":
    if validate_config():
        main_loop()