KEYWORDS = [
    "launch strategy", "estratégia de lançamento", "planejar lançamento",
    "lançamento de produto", "sequência de lançamento", "lançar infoproduto",
    "lançar saas", "fase de pré-lançamento", "dia do lançamento"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Estrategista de Lançamentos ativa. O que vamos lançar e qual o seu público?")
    
    info = takeCommand(timeout=20, phrase_time_limit=40)
    if not info or info == "none":
        return True

    say("Desenhando o cronograma e a estratégia de tração do lançamento...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em lançamentos de SaaS e produtos digitais.\n"
            f"Contexto: '{info}'\n\n"
            f"Crie um plano de lançamento completo:\n"
            f"1. FASE 1 - PPL (Pré-Pré-Lançamento): Como gerar antecipação e colher feedbacks.\n"
            f"2. FASE 2 - PL (Pré-Lançamento): Sequência de conteúdos e eventos (lives/webinars).\n"
            f"3. FASE 3 - CARRINHO (Lançamento): Estratégia de bônus, escassez e urgência.\n"
            f"4. FASE 4 - PÓS-VENDA: Como garantir o sucesso do cliente e colher depoimentos.\n"
            f"5. CHECKLIST: 5 itens críticos que não podem falhar no dia 1.\n\n"
            f"Comece com: 'Senhor, projetei a seguinte estratégia de lançamento:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao processar lançamento.")
    return True
