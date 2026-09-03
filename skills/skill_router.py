import os
import importlib.util
import sys
import json

KEYWORDS = [
    "como eu faço para", "queria usar", "ativar função", "quais skills você tem",
    "me ajude com", "preciso de ajuda com", "como você pode me ajudar",
    "gerenciar habilidades", "usar uma habilidade", "qual função usar",
    "ativar uma skill", "usar uma skill", "procurar função", "ajuda com habilidades"
]

def get_available_skills():
    """Lê a pasta de skills e retorna um resumo das habilidades e suas keywords."""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_dir = os.path.join(BASE_DIR, "skills")
    available_skills = []

    for filename in sorted(os.listdir(skills_dir)):
        if filename.endswith(".py") and not filename.startswith("__") and filename != "skill_router.py":
            skill_path = os.path.join(skills_dir, filename)
            skill_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(skill_name, skill_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "KEYWORDS"):
                    available_skills.append({
                        "name": skill_name,
                        "keywords": module.KEYWORDS[:5]
                    })
            except:
                continue
    return available_skills


def _build_tools_schema(available_skills):
    """
    Constrói o schema de tools no formato OpenAI Function Calling.
    Cada skill vira uma 'function' com descrição gerada a partir das suas keywords.
    Padrão inspirado no Qwen-Agent / BaseTool.
    """
    tools = []
    for skill in available_skills:
        tools.append({
            "type": "function",
            "function": {
                "name": skill["name"],
                "description": (
                    f"Use quando o usuário quiser: {', '.join(skill['keywords'][:3])}. "
                    f"Módulo: {skill['name'].replace('_', ' ')}."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "comando": {
                            "type": "string",
                            "description": "O comando completo do usuário, exatamente como foi dito."
                        }
                    },
                    "required": ["comando"]
                }
            }
        })

    # Tool especial para tarefas complexas / multi-etapa
    tools.append({
        "type": "function",
        "function": {
            "name": "autonomous_agent",
            "description": (
                "Use quando o pedido for complexo, envolver múltiplas etapas "
                "ou exigir orquestração de várias habilidades."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "comando": {
                        "type": "string",
                        "description": "O objetivo completo do usuário."
                    }
                },
                "required": ["comando"]
            }
        }
    })
    return tools


_SYSTEM_ROUTING_PROMPT = (
    "Você é o Roteador de Intenções da Laura. "
    "Analise o pedido do usuário e chame a função mais adequada. "
    "REGRAS CRÍTICAS:\n"
    "1. Para CRIAR/FAZER/GERAR/PRODUZIR vídeo → use 'video_explicativo'.\n"
    "2. Para 'Link na Bio', 'Landing Page', 'Criar Site' → use 'web_page_creator'.\n"
    "3. Para minimizar/interface/HUD/chat/bolinha → use 'system_controller'.\n"
    "4. Para posts, artigos ou perfil pessoal do LinkedIn → use 'linkedin_pro'.\n"
    "5. Se for pedido COMPLEXO com múltiplas etapas → use 'autonomous_agent'.\n"
    "6. Se nenhuma skill se encaixar bem → NÃO chame nenhuma função."
)


def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model  = context.get("model_to_use") if context else None
    skill_manager = context.get("skill_manager") if context else None

    # --- Listar habilidades ---
    if any(w in query.lower() for w in ["quais skills", "quais habilidades", "o que você faz"]):
        skills = get_available_skills()
        names = [s["name"].replace("_", " ") for s in skills]
        say(f"Senhor, eu possuo {len(skills)} habilidades principais, incluindo: "
            + ", ".join(names[:10]) + " e muitas outras de marketing, SEO e automação.")
        say("Posso ajudar com algum tema específico?")
        return True

    # --- Atalho hardcoded: comandos de interface (evita alucinação da IA) ---
    if any(k in query.lower() for k in [
        "chat", "bate papo", "bate-papo", "bolinha",
        "minimizar", "interface", "hud", "comms", "fechar", "sair"
    ]):
        print(f"[SkillRouter] Atalho de interface detectado -> system_controller")
        target = next((s for s in skill_manager.skills if s.__name__ == "system_controller"), None)
        if target:
            return target.execute(query, say, takeCommand, context)

    if not client or not model:
        return False

    available_skills = get_available_skills()

    # ==========================================================================
    # ABORDAGEM 1 — Function Calling (padrão Qwen-Agent / OpenAI Tools API)
    # O modelo escolhe a skill via schema JSON estruturado.
    # Muito mais preciso e menos sujeito a alucinação que o roteamento por texto.
    # ==========================================================================
    try:
        tools = _build_tools_schema(available_skills)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_ROUTING_PROMPT},
                {"role": "user",   "content": query}
            ],
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # Modelo optou por não chamar nenhuma tool → chat geral assume
        if not message.tool_calls:
            print(f"[SkillRouter] Function Calling: nenhuma tool selecionada para '{query[:60]}'")
            return False

        tool_call = message.tool_calls[0]
        target_skill_name = tool_call.function.name.strip().lower()
        print(f"[SkillRouter] Function Calling selecionou: '{target_skill_name}'")

        if target_skill_name == "autonomous_agent":
            say("Identifiquei que este é um pedido complexo. Ativando modo de planejamento de projeto.")

        if skill_manager:
            target = next(
                (s for s in skill_manager.skills if s.__name__ == target_skill_name), None
            )
            if target:
                return target.execute(query, say, takeCommand, context)

        print(f"[SkillRouter] Skill '{target_skill_name}' não encontrada no manager.")
        return False

    except Exception as fc_error:
        # ==========================================================================
        # ABORDAGEM 2 — Fallback: Roteamento por Texto
        # Usado quando o provider não suporta tool_choice (ex: alguns modelos gratuitos).
        # ==========================================================================
        print(f"[SkillRouter] Function Calling indisponível ({type(fc_error).__name__}), "
              f"usando fallback por texto...")

        skills_context = "\n".join([
            f"- {s['name']}: Keywords ({', '.join(s['keywords'])})"
            for s in available_skills
        ])

        fallback_prompt = (
            f"Você é o Roteador de Intenções Estratégico da Laura.\n"
            f"O usuário disse: '{query}'\n\n"
            f"Skills disponíveis:\n{skills_context}\n\n"
            "REGRAS CRÍTICAS:\n"
            "1. Para CRIAR/GERAR vídeo → 'video_explicativo'.\n"
            "2. Para Landing Page/Site → 'web_page_creator'.\n"
            "3. Para interface/HUD → 'system_controller'.\n"
            "4. Se complexo/multi-etapa → 'autonomous_agent'.\n"
            "5. Responda APENAS o nome da skill (ex: web_page_creator) ou 'NONE'."
        )

        try:
            fb_resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": fallback_prompt}]
            )
            target_skill_name = (
                fb_resp.choices[0].message.content.strip().lower().replace(".py", "")
            )

            if target_skill_name == "none":
                return False

            if skill_manager:
                target = next(
                    (s for s in skill_manager.skills if s.__name__ == target_skill_name), None
                )
                if target:
                    if target_skill_name == "autonomous_agent":
                        say("Identificado pedido complexo. Ativando modo de planejamento.")
                    else:
                        print(f"[SkillRouter] Fallback roteou para: {target_skill_name}")
                    return target.execute(query, say, takeCommand, context)

        except Exception as e:
            say("Erro ao rotear sua solicitação.")
            print(f"[SkillRouter] Erro no fallback: {e}")

    return True
