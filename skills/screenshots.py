KEYWORDS = [
    "screenshots", "print de marketing", "print do app", "captura de tela marketing",
    "screenshot para landing page", "print para redes sociais", "gerar prints"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Estrategista de Visual Assets ativa. Para qual plataforma você precisa dessas capturas de tela?")
    
    plataforma = takeCommand(timeout=15, phrase_time_limit=30)
    if not plataforma or plataforma == "none":
        return True

    say("Definindo os ângulos, composições e gatilhos visuais das capturas...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Visual Marketing e Capturas de Alta Performance.\n"
            f"Alvo: '{plataforma}'\n\n"
            f"Sua tarefa é projetar o kit de prints:\n"
            f"1. COMPOSIÇÃO: Quais elementos destacar (Ex: Dashboard, Mobile, Close em feature).\n"
            f"2. CONTEXTUALIZAÇÃO: Uso de Mockups vs Prints Reais.\n"
            f"3. ANOTAÇÕES: Onde colocar setas ou textos explicativos no print.\n"
            f"4. VARIANTES: Prints claros vs escuros para diferentes contextos.\n\n"
            f"Comece com: 'Senhor, projetei a seguinte estratégia de visual assets:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro no módulo de visual assets.")
    return True
