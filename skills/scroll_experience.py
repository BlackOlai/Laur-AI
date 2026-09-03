KEYWORDS = [
    "scroll experience", "experiência de scroll", "parallax", "scroll animation",
    "animação de rolagem", "site imersivo", "narrativa visual", "cinematic web"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Especialista em Scroll Experience ativa. Qual a história que seu site deve contar ao rolar a página?")
    
    historia = takeCommand(timeout=20, phrase_time_limit=40)
    if not historia or historia == "none":
        return True

    say("Projetando a coreografia visual e os gatilhos de animação...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Web Imersiva e Scroll Storytelling.\n"
            f"Objetivo: '{historia}'\n\n"
            f"Sua tarefa é desenhar a experiência:\n"
            f"1. NARRATIVA: Como as informações aparecem em sequência.\n"
            f"2. EFEITOS: Sugestão de Parallax, Sticky elements ou Zoom-on-scroll.\n"
            f"3. TECNOLOGIA: Bibliotecas recomendadas (GSAP, Framer Motion, Lenis).\n"
            f"4. PERFORMANCE: Como manter o scroll suave sem travar o navegador.\n\n"
            f"Comece com: 'Senhor, projetei a seguinte experiência de scroll imersiva:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro no design de scroll.")
    return True
