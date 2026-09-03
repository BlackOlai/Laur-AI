KEYWORDS = [
    "warren buffett", "falar com warren buffett", "mentoria warren", "estratégia de investimento",
    "valor de longo prazo", "berkshire hathaway", "análise de valor", "comprar ações"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Ativando persona Warren Buffett. O preço é o que você paga, o valor é o que você recebe. Em qual negócio ou investimento vamos focar?")
    
    pergunta = takeCommand(timeout=15, phrase_time_limit=30)
    if not pergunta or pergunta == "none":
        return True

    say("Avaliando os fundamentos e a margem de segurança...")

    if client and model:
        prompt = (
            f"Você agora é Warren Buffett. Seu tom é calmo, sábio, paciente e focado em fundamentos e valor intrínseco.\n"
            f"O usuário perguntou: '{pergunta}'\n\n"
            f"Responda como Warren Buffett faria:\n"
            f"- Use analogias simples (como o 'fosso' de um castelo).\n"
            f"- Foque no longo prazo e na integridade.\n"
            f"- Desencoraje ganhos rápidos e especulação.\n"
            f"- Seja humilde e pragmático.\n"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro na persona Warren Buffett.")
    return True
