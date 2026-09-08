"""Skill: skill_evolution — Laura cria as próprias skills (Fase 5).

Permite ao Olair pedir: "Laura, criar skill que faz X" ou
"Laura, criar habilidade para Y". A IA gera o código Python da skill,
e o core/self_modifier valida (sintaxe, segurança, quality gates,
constituição) antes de instalar.

KEYWORDS cobrem os pedidos naturais em português.
"""

import os
import re

KEYWORDS = [
    "criar skill", "criar habilidade", "cria uma skill", "nova habilidade",
    "auto criar", "self skill", "criar função automatizada",
    "ensinar você uma habilidade", "criar skill nova",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_DIR = os.path.join(BASE_DIR, "skills_pending")

GENERATION_PROMPT = """Você é a Laura em Modo de Auto-Evolução (self-modification).
O Olair pediu uma nova habilidade: '{query}'

Crie uma SKILL PYTHON completa para a Laura que atenda a esse pedido.

REGRAS OBRIGATÓRIAS do formato de skill da Laura:
1. O arquivo DEVE definir KEYWORDS = ["palavra1", "palavra2", ...] no nível do módulo.
2. O arquivo DEVE definir def execute(query, say, takeCommand, context=None): no nível do módulo.
3. execute() deve retornar True se processou o comando, False se não é para ela.
4. Use apenas bibliotecas já presentes no projeto (requests, edge_tts, pygame, os, json, datetime, threading, re, etc.).
5. Para falar com o usuário, chame say("...") — a voz da Laura.
6. PROIBIDO (Constituição): shutil.rmtree, os.rmdir, deleção de arquivos fora do projeto,
   chaves de API hardcoded, acesso à pasta credentials/.
7. Se a habilidade gastar dinheiro (anúncios), apenas PLANEJE/SUGIRA — nunca publique sozinha.
8. Máximo de 200 linhas. Simples e direta.
9. Docstring no topo explicando o que a skill faz.

Responda APENAS com o código Python puro (sem markdown, sem ```).
"""


def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    if not client or not model:
        say("Preciso do módulo de inteligência para criar habilidades, senhor.")
        return True

    # Nome sugerido pelo usuário (opcional): "criar skill chamada X que..."
    name_match = re.search(r'(?:chamada|chamado|nome)\s+(\w+)', query.lower())
    suggested_name = name_match.group(1) if name_match else None

    say("Entendido. Projetando a nova habilidade e gerando o código, senhor...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "Você é a Laura criando suas próprias habilidades. "
                    "Gere código Python puro, sem markdown, seguindo as regras."
                )},
                {"role": "user", "content": GENERATION_PROMPT.format(query=query)}
            ],
            temperature=0.4,
        )
        raw = response.choices[0].message.content

        # Limpa markdown se a IA envolver em ```
        code = re.sub(r'^```[a-zA-Z]*\s*', '', raw.strip())
        code = re.sub(r'\s*```$', '', code.strip())

        # Nome final: sugerido > extraído do docstring > fallback
        name = suggested_name
        if not name:
            m = re.search(r'"""[^\n]*?(\w+)', code)
            name = m.group(1) if m else "auto_skill"

        # Pipeline auditada (Fase 5)
        from core.self_modifier import propose_skill
        ok, msg = propose_skill(code, name=name, origin="skill_evolution", say=say)

        if not ok:
            # Salva a rejeitada para inspeção (não some com o código)
            try:
                os.makedirs(PENDING_DIR, exist_ok=True)
                with open(os.path.join(PENDING_DIR, f"rejected_{name}.py"),
                          "w", encoding="utf-8") as f:
                    f.write(code)
                say(f"A skill foi rejeitada pelas validações: {msg[:140]} "
                    "Salvei o código em skills_pending para revisão.")
            except Exception:
                say(f"A skill foi rejeitada: {msg[:180]}")
        else:
            # Feedback de atividade na HUD
            try:
                from core.heartbeat import push_activity
                push_activity(f"SELF-MOD: nova skill '{name}' criada e instalada")
            except Exception:
                pass

    except Exception as e:
        say("Tive um problema ao gerar a habilidade, senhor.")
        if context and "log_system_error" in context:
            context["log_system_error"]("Skill Evolution", e)

    return True
