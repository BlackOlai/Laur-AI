KEYWORDS = [
    "social media hub", "gerenciador de redes sociais", "criar posts",
    "post para instagram", "post para linkedin", "roteiro para youtube",
    "calendário editorial", "estratégia de conteúdo", "escritor social",
    "social writer", "gerar conteúdo", "copy para rede social"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    say("Social Media Hub ativado. Para qual rede social vamos criar hoje?")
    say("1 - Instagram | 2 - LinkedIn | 3 - YouTube/Reels | 4 - Calendário Mensal")

    opcao = takeCommand(timeout=15)
    if not opcao or opcao == "none":
        return True

    say("Sobre qual tema ou produto vamos criar o conteúdo?")
    contexto = takeCommand(timeout=25)
    if not contexto or contexto == "none":
        return True

    say("Gerando conteúdo criativo e otimizado para engajamento...")

    if client and model:
        prompt_base = f"Você é Laura, Especialista em Redes Sociais e Viralização. Tema: {contexto}\n\n"
        
        if "1" in opcao or "instagram" in opcao:
            prompt = prompt_base + "Crie 3 opções de posts para Instagram (Legenda + Ideia Visual + Hashtags) focados em engajamento."
        elif "2" in opcao or "linkedin" in opcao:
            prompt = prompt_base + "Escreva um post de autoridade para o LinkedIn, com tom profissional e focado em gerar conversas."
        elif "3" in opcao or "youtube" in opcao or "reels" in opcao or "video" in opcao:
            prompt = prompt_base + "Crie um roteiro curto (script) para um vídeo de 60 segundos focado em prender a atenção (Hook, Body, CTA)."
        elif "4" in opcao or "calendário" in opcao:
            prompt = prompt_base + "Monte um calendário editorial de 7 dias com temas variados para manter a consistência."
        else:
            prompt = prompt_base + "Crie uma estratégia de conteúdo multiplataforma."

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao acessar o módulo de redes sociais.")
            
    return True
