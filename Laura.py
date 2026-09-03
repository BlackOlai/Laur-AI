import os
import time
import datetime
import json
import threading
import random
from dotenv import load_dotenv
from openai import OpenAI

# Imports do Core System (Modular)
from core.stt import takeCommand
from core.tts import say
from core.status import set_status
from core.skill_manager import SkillManager
from core.config_manager import validate_config
from core.memory_manager import MemoryManager
from core.mcp_manager import MCPManager

# Carregar configurações
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CONFIGURAÇÃO DO MOTOR DE IA (GROQ PRIORIDADE) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_ai_client():
    """Define o cliente e modelo baseado na prioridade: Groq > NVIDIA > OpenRouter."""
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
    print(f"[Warning] Falha ao inicializar o banco de memórias: {e}")
    memory_manager = None

try:
    mcp_manager = MCPManager()
except Exception as e:
    print(f"[Warning] Falha ao inicializar o MCP Manager: {e}")
    mcp_manager = None

# --- MEMÓRIA DE SESSÃO (padrão Qwen-Agent) ---
# Histórico multi-turno da sessão atual. Mantemos no máximo MAX_HISTORY pares
# de mensagens para não estourar o contexto do modelo.
MAX_HISTORY_MESSAGES = 20  # 10 turnos (user + assistant cada)
conversation_history = []

def log_system_error(origin, error):
    log_file = os.path.join(BASE_DIR, "error_logs.json")
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except: logs = []
    logs.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "origin": origin, "message": str(error), "status": "unread"
    })
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

def chat(query):
    """Chat de IA geral com memória de sessão multi-turno.
    
    Mantém um histórico rolante da conversa (conversation_history) para que
    a Laura lembre o que foi dito anteriormente na mesma sessão — padrão
    inspirado no Qwen-Agent.
    """
    global conversation_history
    try:
        set_status("thinking", "Processando...")

        # Recuperar memória do passado baseada na query atual
        memories = ""
        if memory_manager:
            results = memory_manager.search_memory(query, k=3)
            if results:
                memories = "\n--- MEMÓRIAS RELEVANTES DO PASSADO ---\n"
                for res in results:
                    memories += f"- {res['text']}\n"

        system_content = (
            "Você é a Laura, uma assistente de elite e parceira estratégica do Olair. "
            "Trate o Olair diretamente, com respeito mas com a proximidade de uma parceira de alto nível. "
            "Nunca fale de si mesma na terceira pessoa e nunca trate o usuário na terceira pessoa. "
            "Seja inteligente, direta e proativa. "
            "Você tem memória desta conversa — use-a para manter contexto e coerência."
        )

        if memories:
            system_content += f"\n\n{memories}\nUse essas memórias passadas se forem úteis para responder."

        # Monta o payload com histórico de sessão completo
        messages = [
            {"role": "system", "content": system_content},
            *conversation_history,          # ← histórico da sessão atual
            {"role": "user", "content": query}
        ]

        # Adicionar ferramentas MCP se disponíveis
        tools = mcp_manager.get_tools() if mcp_manager else []
        
        kwargs = {"model": model_to_use, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        # Processar tool calls (se o LLM decidiu usar uma ferramenta MCP)
        if hasattr(message, "tool_calls") and message.tool_calls:
            set_status("thinking", "Executando ferramenta MCP...")
            
            # Precisamos converter a Message object para dict ou adicioná-la diretamente
            messages.append(message)
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except Exception:
                    arguments = {}
                
                print(f"[MCP] Executando: {function_name} com args {arguments}")
                tool_result = mcp_manager.call_tool(function_name, arguments)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(tool_result)
                })
                
            # Segunda chamada ao LLM (com o resultado da ferramenta)
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages
            )
            res = response.choices[0].message.content
        else:
            res = message.content

        # Atualiza o histórico com a troca atual
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": res})

        # Limpa histórico antigo para não estourar contexto do modelo
        if len(conversation_history) > MAX_HISTORY_MESSAGES:
            conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]

        # Salva o diálogo atual na memória de longo prazo (invisível pro usuário)
        if memory_manager:
            threading.Thread(
                target=memory_manager.add_memory, 
                args=(f"O Olair disse: '{query}'. A Laura respondeu: '{res}'", "chat_auto"),
                daemon=True
            ).start()

        say(res)

    except Exception as e:
        log_system_error("Chat Fallback", e)
        say("Olair, tive um pequeno problema de conexão com meu cérebro agora.")

def main_loop():
    # Inicia tarefas de background (Clima, Notícias, etc)
    threading.Thread(target=background_tasks, daemon=True).start()

    # Inicia o Heartbeat (executa tarefas agendadas vencidas a cada 30s)
    try:
        from core.heartbeat import start_heartbeat
        start_heartbeat(say)
    except Exception as e:
        print(f"[Warning] Falha ao iniciar o heartbeat: {e}")
    
    # Saudações dinâmicas
    hora = datetime.datetime.now().hour
    saudacoes_bomdia = ["Bom dia, Olair!", "Olá Olair, bom dia! Pronta para ajudar."]
    saudacoes_boatarde = ["Boa tarde, Olair! Como posso ser útil?", "Boa tarde, senhor! Em que trabalhamos agora?"]
    saudacoes_boanoite = ["Boa noite, Olair!", "Boa noite, senhor! No que posso ajudar?"]
    
    if 5 <= hora < 12: msg = random.choice(saudacoes_bomdia)
    elif 12 <= hora < 18: msg = random.choice(saudacoes_boatarde)
    else: msg = random.choice(saudacoes_boanoite)
    
    # Pequeno delay para o sistema de áudio e HUD estabilizarem
    time.sleep(2)
    say(msg)
    
    continuous_mode = False
    last_interaction_time = 0

    while True:
        try:
            # Controle de modo contínuo (janela de 7s para não precisar repetir o nome)
            if continuous_mode and (time.time() - last_interaction_time < 7):
                raw_query, source = takeCommand(timeout=3, return_source=True)
                if not raw_query or raw_query == "none":
                    continuous_mode = False
                    set_status("idle", "")
                    continue
                # No modo contínuo, qualquer mensagem do chat é aceita diretamente
                if source == "widget" or "http" in raw_query:
                    print(f"[DEBUG] Contínuo via {source}: {raw_query}")
                    query = raw_query.replace("laura", "").strip()
                elif "laura" in raw_query:
                    query = raw_query.replace("laura", "").strip()
                    if not query:
                        say("Sim, Olair?")
                        raw_query2, _ = takeCommand(timeout=5, return_source=True)
                        query = raw_query2
                else:
                    # Em modo contínuo, aceita qualquer coisa (sem precisar dizer "Laura")
                    query = raw_query
            else:
                continuous_mode = False
                set_status("idle", "")
                raw_query, source = takeCommand(timeout=None, return_source=True)
                
                if not raw_query or raw_query == "none": continue
                
                # Se vier do Widget, aceita qualquer coisa (bypass keyword 'Laura')
                if source == "widget" or "http" in raw_query:
                    print(f"[DEBUG] Comando recebido via {source}: {raw_query}")
                    query = raw_query.replace("laura", "").strip()
                elif "laura" in raw_query:
                    query = raw_query.replace("laura", "").strip()
                    if not query:
                        say("Sim, Olair?")
                        raw_query2, _ = takeCommand(timeout=5, return_source=True)
                        query = raw_query2
                else: continue

            if not query or query == "none": continue

            # Interrupções e controle de memória
            if any(cmd in query for cmd in ["parar", "silêncio", "pare", "cancelar"]):
                say("Certo.")
                continuous_mode = False
                continue

            # Limpar memória de sessão por comando de voz
            if any(cmd in query for cmd in ["limpar memória", "esquecer conversa", "nova conversa", "resetar contexto"]):
                conversation_history.clear()
                say("Memória de sessão limpa. Começando do zero, Olair.")
                continuous_mode = False
                continue

            context = {
                "say": say, "takeCommand": takeCommand, "set_status": set_status,
                "log_system_error": log_system_error, "client": client,
                "model_to_use": model_to_use, "skill_manager": skill_manager,
                "memory_manager": memory_manager,
                # Memória de sessão — disponível para skills que precisem de contexto
                "conversation_history": conversation_history,
                "clear_history": lambda: conversation_history.clear()
            }

            # --- PROCESSAMENTO DE COMANDOS ---
            
            # 1. Match Direto de Keywords (Habilidades do Sistema)
            if skill_manager.handle(query, say, takeCommand, context):
                continuous_mode = True
                last_interaction_time = time.time()
                continue
            
            # --- REFORÇO DE SEGURANÇA: Se for um link e o SkillManager falhou, força a análise ---
            if "http" in query.lower():
                try:
                    from skills.link_analyzer import execute as link_exec
                    if link_exec(query, say, takeCommand, context):
                        continuous_mode = True
                        last_interaction_time = time.time()
                        continue
                except Exception as e:
                    print(f"[REFORÇO] Falha ao forçar link_analyzer: {e}")

            # 2. Roteador Estratégico (IA decide a Skill)
            from skills.skill_router import execute as route_intent
            if route_intent(query, say, takeCommand, context):
                continuous_mode = True
                last_interaction_time = time.time()
            else:
                # 3. Chat de Inteligência Geral
                chat(query)
                continuous_mode = True
                last_interaction_time = time.time()

        except Exception as e:
            log_system_error("Main Loop", e)
            time.sleep(1)

def background_tasks():
    """Tarefas que rodam em segundo plano (Clima, Notícias, Google Calendar, etc)."""
    print("[Background] Iniciando tarefas de monitoramento (Clima/Mercado/Calendar)...")
    try:
        from skills.info_services import update_widget_cache
    except Exception as e:
        print(f"[Background Error] Falha ao importar info_services: {e}")
        return

    while True:
        try:
            # Atualiza dados do widget (Clima e Mercado)
            print("[Background] Buscando atualizações de Clima e Mercado...")
            data = update_widget_cache()
            if data:
                print(f"[Background] Sucesso: Dados atualizados às {data.get('updated')}")
            else:
                print("[Background Warning] update_widget_cache retornou vazio.")
        except Exception as e:
            print(f"[Background Error] Erro na execução: {e}")

        # Verifica tarefas de produção no Google Calendar
        try:
            from skills.google_calendar import check_production_tasks
            print("[Background] Verificando tarefas de produção no Google Calendar...")
            check_production_tasks(client, model_to_use, say, takeCommand, skill_manager)
        except ImportError:
            pass  # Bibliotecas do Google não instaladas — ignora silenciosamente
        except Exception as e:
            print(f"[Background] Erro ao verificar Google Calendar: {e}")
        
        # Aguarda 15 minutos para a próxima atualização
        time.sleep(900)

if __name__ == "__main__":
    if validate_config():
        main_loop()
