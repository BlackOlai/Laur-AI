KEYWORDS = [
    "competitor intelligence", "analisar concorrente", "espionar concorrente",
    "inteligência competitiva", "estratégia da concorrência", "analisar mercado",
    "benchmark", "pontos fortes e fracos"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Módulo de Inteligência Competitiva ativado. Qual concorrente ou nicho devo analisar?")
    
    concorrente = takeCommand(timeout=15, phrase_time_limit=30)
    if not concorrente or concorrente == "none":
        return True

    say(f"Mapeando presença digital e estratégias de {concorrente}...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Inteligência de Mercado e Benchmarking.\n"
            f"Alvo da análise: '{concorrente}'\n\n"
            f"Forneça um relatório estratégico cobrindo:\n"
            f"1. POSICIONAMENTO: Como eles se vendem no mercado.\n"
            f"2. CANAIS: Onde eles são mais fortes (SEO, Ads, Social).\n"
            f"3. PONTOS FORTES: O que eles fazem muito bem.\n"
            f"4. PONTOS FRACOS (BRECHAS): Onde você pode atacá-los e ganhar mercado.\n"
            f"5. SUGESTÃO DE CONTRA-ATAQUE: Uma ação prática para superar esse concorrente.\n\n"
            f"Seja crítico e analítico. Comece com: 'Senhor, aqui está o dossiê da concorrência:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao analisar concorrência.")
    return True
