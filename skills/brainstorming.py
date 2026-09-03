import re

KEYWORDS = [
    "brainstorm", "brainstorming", "explorar ideias", "me ajude a pensar",
    "gerar ideias", "ideias para", "vamos pensar", "sugestões para",
    "me dê ideias", "o que você acha de", "pensar em alternativas"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    # Extrair o tópico da query
    topic = query
    for kw in KEYWORDS:
        topic = topic.lower().replace(kw, "").strip()
    topic = topic.strip(" .,?!")

    if not topic:
        say("Claro, vamos explorar ideias! Sobre qual assunto ou projeto você quer fazer um brainstorming?")
        topic = takeCommand(timeout=10, phrase_time_limit=15)
        if not topic or topic == "none":
            say("Não entendi o tema. Por favor, tente novamente.")
            return True

    say(f"Ativando modo criativo. Gerando ideias para: {topic}. Um momento, senhor...")

    if client and model:
        prompt = (
            f"Você é Laura, uma IA criativa e estratégica. O usuário quer fazer um brainstorming sobre:\n"
            f"TEMA: {topic}\n\n"
            f"Gere entre 5 e 7 ideias concretas, variadas e criativas.\n"
            f"Para cada ideia, dê um nome curto e uma explicação de 1-2 frases.\n"
            f"Use um tom empolgante, direto e inspirador.\n"
            f"Comece com: 'Senhor, aqui estão minhas sugestões:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            ideas = response.choices[0].message.content
            say(ideas)
        except Exception as e:
            say("Desculpe, tive um problema ao gerar as ideias. Tente novamente.")
            if context and "log_system_error" in context:
                context["log_system_error"]("Brainstorming Skill", e)
    else:
        say(f"Não consigo acessar meu módulo criativo agora. Verifique a conexão com a API.")

    return True
