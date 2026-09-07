"""Motor de conversación general de la Laura (extraído de Laura.py — refactor prompt 09).

chat() es la capa de fallback: cuando ninguna skill/router resuelve la
intención, la Laura conversa libremente con memoria de sesión multi-turno
(histórico rolante) + memoria de largo plazo (ChromaDB) + herramientas MCP.

Extraído preservando la interfaz original; las dependencias se pasan
explícitamente via `deps` para romper el acoplamiento a globals de Laura.py.
"""
import json
import threading


def chat(query, deps, conversation_history, MAX_HISTORY_MESSAGES):
    """Chat de IA general con memoria de sesión multi-turno.

    deps: dict con {client, model_to_use, memory_manager, mcp_manager,
                    set_status, say, log_system_error, persist_chat_history}
    """
    client = deps["client"]
    model_to_use = deps["model_to_use"]
    memory_manager = deps.get("memory_manager")
    mcp_manager = deps.get("mcp_manager")
    set_status = deps["set_status"]
    log_system_error = deps["log_system_error"]
    persist = deps.get("persist_chat_history")

    try:
        set_status("thinking", "Procesando...")

        # Recuperar memoria del pasado basada en la query actual
        memories = ""
        if memory_manager:
            results = memory_manager.search_memory(query, k=3)
            if results:
                memories = "\n--- MEMORIAS RELEVANTES DEL PASADO ---\n"
                for res in results:
                    memories += f"- {res['text']}\n"

        system_content = (
            "Eres Laura, una asistente de élite y socia estratégica de Olair. "
            "Trata a Olair directamente, con respeto pero con la cercanía de una socia de alto nivel. "
            "Nunca hables de ti misma en tercera persona ni trates al usuario en tercera persona. "
            "Sé inteligente, directa y proactiva. "
            "Tienes memoria de esta conversación — úsala para mantener contexto y coherencia."
        )

        # Constituição (Fase 4): leis imutáveis guiam as sugestões da Laura
        try:
            from core.constitution import get_rules_summary
            system_content += "\n\n" + get_rules_summary() + (
                "\nSe Olair pedir algo que viole uma lei, explique a lei e "
                "ofereça a alternativa segura (ex.: sugerir campanha sem publicar)."
            )
        except Exception as e:
            print(f"[ChatEngine] Constituição indisponível: {e}")

        if memories:
            system_content += f"\n\n{memories}\nUsa estas memorias pasadas si son útiles para responder."

        # Monta el payload con histórico de sesión completo
        messages = [
            {"role": "system", "content": system_content},
            *conversation_history,          # ← histórico de la sesión actual
            {"role": "user", "content": query}
        ]

        # Añadir herramientas MCP si disponibles
        tools = mcp_manager.get_tools() if mcp_manager else []
        kwargs = {"model": model_to_use, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        # Procesar tool calls (si el LLM decidió usar una herramienta MCP)
        if hasattr(message, "tool_calls") and message.tool_calls:
            set_status("thinking", "Ejecutando herramienta MCP...")
            messages.append(message)
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except Exception:
                    arguments = {}
                print(f"[MCP] Ejecutando: {function_name} con args {arguments}")
                tool_result = mcp_manager.call_tool(function_name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(tool_result)
                })
            # Segunda llamada al LLM (con el resultado de la herramienta)
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages
            )
            res = response.choices[0].message.content
        else:
            res = message.content

        # Actualiza el histórico con el intercambio actual
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": res})
        if len(conversation_history) > MAX_HISTORY_MESSAGES:
            del conversation_history[:-MAX_HISTORY_MESSAGES]

        # Persistir el histórico para la HUD (el chat del widget abre con memoria)
        if persist:
            persist(query, res)

        # Guarda el diálogo actual en la memoria de largo plazo (invisible para el usuario)
        if memory_manager:
            threading.Thread(
                target=memory_manager.add_memory,
                args=(f"Olair dijo: '{query}'. Laura respondió: '{res}'", "chat_auto"),
                daemon=True
            ).start()

        deps["say"](res)

    except Exception as e:
        log_system_error("Chat Fallback", e)
        deps["say"]("Olair, tuve un pequeño problema de conexión con mi cerebro ahora.")