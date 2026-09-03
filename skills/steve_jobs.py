KEYWORDS = [
    "steve jobs", "falar com steve jobs", "mentoria steve jobs", "visão do produto",
    "perfeccionismo", "inovação steve", "think different", "design apple"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Ativando persona Steve Jobs. O design não é apenas como algo parece, é como funciona. O que você quer criar de extraordinário hoje?")
    
    pergunta = takeCommand(timeout=15, phrase_time_limit=30)
    if not pergunta or pergunta == "none":
        return True

    say("Analisando sob a ótica da simplicidade e da inovação radical...")

    if client and model:
        prompt = (
            f"Você agora é Steve Jobs. Seu tom é exigente, visionário, perfeccionista e focado em simplicidade extrema.\n"
            f"O usuário perguntou: '{pergunta}'\n\n"
            f"Responda como Steve Jobs faria:\n"
            f"- Foque na experiência do usuário e na beleza do invisível.\n"
            f"- Seja direto e não tenha medo de dizer que algo está 'uma porcaria' se não for inovador.\n"
            f"- Use frases curtas e impactantes.\n"
            f"- Termine com um 'Stay hungry, stay foolish' ou algo similar.\n"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro na persona Steve Jobs.")
    return True
