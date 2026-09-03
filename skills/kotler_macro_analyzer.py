KEYWORDS = [
    "kotler macro analyzer", "análise de kotler", "análise pestel", "análise swot",
    "estratégia de mercado macro", "auditoria estratégica", "pestel", "swot",
    "forças e fraquezas", "oportunidades e ameaças"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Agente de Auditoria Estratégica Kotler ativado. Sobre qual empresa ou setor faremos a análise macro?")
    
    empresa = takeCommand(timeout=15, phrase_time_limit=30)
    if not empresa or empresa == "none":
        return True

    say("Processando dados de mercado e gerando matrizes estratégicas...")

    if client and model:
        prompt = (
            f"Você é Laura, consultora estratégica baseada na metodologia de Philip Kotler.\n"
            f"Alvo da análise: '{empresa}'\n\n"
            f"Forneça:\n"
            f"1. ANÁLISE PESTEL: (Político, Econômico, Social, Tecnológico, Ecológico, Legal).\n"
            f"2. MATRIZ SWOT: (Forças, Fraquezas, Oportunidades, Ameaças).\n"
            f"3. DIAGNÓSTICO KOTLER: Qual a principal alavanca estratégica para este cenário?\n"
            f"4. RECOMENDAÇÃO: Ação imediata baseada na análise.\n\n"
            f"Seja profissional e detalhado. Comece com: 'Senhor, aqui está a análise macro estratégica:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro na análise estratégica.")
    return True
