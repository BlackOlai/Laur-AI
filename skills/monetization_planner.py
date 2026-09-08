# -*- coding: utf-8 -*-
"""Skill: monetization_planner — plano de monetização sem investimento.

Rotina que conecta as skills de estratégia existentes numa única entrega:
ideias de produtos digitais sem custo inicial, escolha recomendada,
precificação, canais orgânicos gratuitos e sequência de lançamento de 7 dias.

Produz um plano em Markdown salvo em planos_monetizacao/ e retorna o
resultado no protocolo estruturado (Fase 2.5) para a pipeline autônoma.
"""
import os
import datetime

KEYWORDS = [
    "ganhar dinheiro na internet", "ganhar dinheiro sem investir",
    "monetização sem investimento", "plano de monetização",
    "renda extra online", "como ganhar dinheiro", "monetizar sem custo",
    "produto digital com alto potencial", "plano de renda",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANOS_DIR = os.path.join(BASE_DIR, "planos_monetizacao")

PROMPT_PLANO = """Você é estrategista de monetização digital sênior da MG Solution.
O usuário (Olair) quer gerar renda online SEM investimento inicial.

TEMA/CONTEXTO FORNECIDO: '{tema}'

Gere um plano de monetização em Markdown (PT-BR) com EXATAMENTE estas seções:

## 1. Diagnóstico rápido
Por que este tema/nicho tem potencial agora (2-3 linhas).

## 2. Cinco produtos digitais sem investimento inicial
Para cada um: nome, formato (ebook/template/notion/free tool/mini-curso),
esforço estimado (baixo/médio) e por que não custa nada produzir.
Use apenas ferramentas gratuitas (Canva free, Google Docs, Notion, GitHub Pages...).

## 3. Recomendação única
Escolha UM produto com melhor relação esforço x potencial e justifique em 3 linhas.

## 4. Precificação sugerida
Preço de lançamento, preço cheio e um upsell simples. Justifique os números.

## 5. Canais de distribuição 100% gratuitos
3 canais orgânicos (ex.: TikTok/Shorts, LinkedIn, grupos de nicho) com tática concreta.

## 6. Sequência de lançamento — 7 dias
Dia a dia (Dia 1 ... Dia 7) com ação específica e meta de cada dia.

## 7. Próximos passos com a Laura
Quais habilidades dela executam cada parte (ex.: 'Laura, criar ebook sobre X').

Seja concreto e acionável. Nada de generalidades."""


def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    if not client or not model:
        say("Preciso do módulo de inteligência para montar o plano, senhor.")
        return True

    # Extrai o tema: remove keywords do pedido e palavras de comando comuns
    tema = query.strip()
    for kw in KEYWORDS:
        tema = tema.lower().replace(kw, "").strip(" ,.:!?")
    # Limpa palavras de comando/verbosidade que sobram no início
    palavras_ruido = ["laura", "quero", "queria", "preciso", "me", "faça", "faz",
                      "crie", "criar", "monte", "montar", "um", "uma", "o", "a",
                      "para", "de", "sobre", "agora", "por favor", "como", "qual"]
    palavras = [p for p in tema.split() if p.strip(",.:!?") not in palavras_ruido]
    tema = " ".join(palavras).strip()

    if not tema:
        say("Sobre qual nicho ou habilidade sua o senhor quer monetizar?")
        resposta = takeCommand()
        if not resposta or resposta.lower() == "none":
            say("Sem problema. Podemos tentar depois, senhor.")
            return True
        tema = resposta.strip()

    say(f"Montando seu plano de monetização sem investimento sobre '{tema}'. "
        "Vou mapear produtos, preços e lançamento de 7 dias...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "Você é estrategista de monetização digital sênior. "
                    "Responde em PT-BR, concreto e acionável."
                )},
                {"role": "user", "content": PROMPT_PLANO.format(tema=tema)},
            ],
            temperature=0.7,
        )
        plano_md = response.choices[0].message.content or ""
        plano_md = plano_md.replace("```markdown", "").replace("```", "").strip()

        # Salva o plano como artefato
        os.makedirs(PLANOS_DIR, exist_ok=True)
        slug = "".join(c if c.isalnum() else "_" for c in tema.lower())[:40].strip("_") or "plano"
        filename = f"plano_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}_{slug}.md"
        filepath = os.path.join(PLANOS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Plano de Monetização — {tema}\n\n"
                    f"Gerado pela Laura em {datetime.datetime.now():%d/%m/%Y %H:%M}\n\n"
                    + plano_md)

        say(f"Plano concluído e salvo em planos_monetização, senhor. "
            f"Destaque: {plano_md[:180]}...")

        # Feedback na HUD
        try:
            from core.heartbeat import push_activity
            push_activity(f"PLANO DE MONETIZAÇÃO '{tema[:40]}' salvo em {filename}")
        except Exception as _e:
            print(f"[MonetizationPlanner] Sem feed da HUD: {_e}")

        # Protocolo estruturado (Fase 2.5) para a pipeline autônoma
        try:
            from core.skill_protocol import ok
            return ok(
                data={"tema": tema, "resumo": plano_md[:2000]},
                artifacts=[filepath],
                summary=f"Plano de monetização '{tema}' gerado: {filename}",
            )
        except ImportError:
            return True

    except Exception as e:
        say("Tive um problema ao montar o plano de monetização, senhor.")
        if context and "log_system_error" in context:
            context["log_system_error"]("MonetizationPlanner", e)
        try:
            from core.skill_protocol import fail
            return fail(f"MonetizationPlanner: {e}")
        except ImportError:
            return True