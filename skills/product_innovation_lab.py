KEYWORDS = [
    "product innovation", "laboratório de produto", "criar produto",
    "design de produto", "inventor de produtos", "product manager",
    "gerente de produto", "toolkit de produto", "validar ideia",
    "mvp", "roadmap de produto", "protótipo"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    say("Laboratório de Inovação ativado. Qual a ideia de produto que vamos desenvolver?")
    say("1 - Inventar/Refinar Ideia | 2 - Design & UX | 3 - Planejamento PM (Roadmap/MVP)")

    opcao = takeCommand(timeout=15)
    if not opcao or opcao == "none":
        return True

    say("Descreva sua ideia ou o problema que o produto resolve.")
    contexto = takeCommand(timeout=25)
    if not contexto or contexto == "none":
        return True

    say("Iniciando processo de design thinking e modelagem de produto...")

    if client and model:
        prompt_base = f"Você é Laura, Product Designer e Manager Sênior. Ideia: {contexto}\n\n"
        
        if "1" in opcao or "inventar" in opcao or "refinar" in opcao:
            prompt = prompt_base + "Refine esta ideia de produto. Crie um nome, uma Proposta Única de Valor (UVP) e liste as 5 funcionalidades principais."
        elif "2" in opcao or "design" in opcao or "ux" in opcao:
            prompt = prompt_base + "Desenhe a experiência do usuário. Como deve ser o fluxo principal e quais elementos visuais trazem mais confiança e usabilidade?"
        elif "3" in opcao or "pm" in opcao or "roadmap" in opcao or "mvp" in opcao:
            prompt = prompt_base + "Defina o MVP (Mínimo Produto Viável). O que é essencial para lançar agora e qual o roadmap para os próximos 3 meses?"
        else:
            prompt = prompt_base + "Faça uma análise completa de viabilidade e design de produto."

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao acessar o módulo de produto.")
            
    return True
