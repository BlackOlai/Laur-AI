KEYWORDS = [
    "free tool strategy", "ferramenta gratuita como marketing", "gerar leads com ferramentas",
    "freebie técnico", "lead magnet", "estratégia de ferramenta grátis",
    "engenharia como marketing", "free tool", "atrair tráfego orgânico"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Estrategista de 'Engineering as Marketing' ativa. Qual o nicho ou problema do seu público que queremos resolver com uma ferramenta gratuita?")
    
    contexto = takeCommand(timeout=15, phrase_time_limit=30)
    if not contexto or contexto == "none":
        return True

    say("Analisando brechas de mercado e projetando ferramentas de alto valor...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em estratégia de 'Engineering as Marketing'.\n"
            f"O contexto é: '{contexto}'\n\n"
            f"Sua tarefa é sugerir 3 ideias de ferramentas gratuitas que gerem leads:\n"
            f"1. IDEIA SIMPLES: Algo que possa ser feito rápido (Ex: uma calculadora, um checklist interativo).\n"
            f"2. IDEIA MÉDIA: Algo com mais valor (Ex: um gerador de templates, um auditor básico).\n"
            f"3. IDEIA COMPLEXA: Uma ferramenta 'uau' (Ex: um mini-app funcional, análise via IA).\n\n"
            f"Para cada uma indique: O valor para o usuário, o custo de desenvolvimento e como ela captura o lead.\n"
            f"Comece com: 'Senhor, projetei as seguintes estratégias de ferramentas gratuitas:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao processar estratégia.")
    return True
