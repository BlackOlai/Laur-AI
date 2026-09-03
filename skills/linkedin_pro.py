KEYWORDS = [
    "linkedin pro", "especialista linkedin", "otimizar perfil linkedin",
    "autoridade no linkedin", "linkedin master",
    "headline do linkedin", "banner do linkedin", "artigo linkedin",
    "post de autoridade linkedin"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    say("LinkedIn Pro ativado. Como posso elevar sua autoridade hoje?")
    say("1 - Otimizar Perfil (Bio/Sobre) | 2 - Criar Post de Autoridade | 3 - Idéias de Banner e Visual")

    opcao = takeCommand(timeout=15)
    if not opcao or opcao == "none":
        return True

    say("Qual o seu cargo atual ou o objetivo do seu perfil?")
    contexto = takeCommand(timeout=20)
    if not contexto or contexto == "none":
        return True

    say("Analisando tendências do LinkedIn e otimizando seu posicionamento...")

    if client and model:
        prompt_base = f"Você é Laura, Especialista em Personal Branding no LinkedIn. Contexto: {contexto}\n\n"
        
        if "1" in opcao or "perfil" in opcao:
            prompt = prompt_base + "Escreva uma Headline (Título) magnética e uma seção 'Sobre' (About) focada em conquistas e palavras-chave."
        elif "2" in opcao or "post" in opcao:
            prompt = prompt_base + "Crie um post de autoridade para o LinkedIn usando o método 'Hook-Story-Lesson-CTA'."
        elif "3" in opcao or "banner" in opcao:
            prompt = prompt_base + "Sugira uma identidade visual para o Banner e quais elementos devem aparecer na foto de perfil para transmitir confiança."
        else:
            prompt = prompt_base + "Dê dicas gerais para aumentar o alcance e o Social Selling Index (SSI) no LinkedIn."

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao acessar o módulo LinkedIn.")
            
    return True
