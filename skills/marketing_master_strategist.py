KEYWORDS = [
    "estrategista de marketing", "marketing master", "plano de marketing",
    "growth engine", "ideias de marketing", "gatilhos mentais", "psicologia do marketing",
    "analisar público", "criar persona", "avatar", "estratégia de crescimento",
    "como crescer meu negócio", "funil de vendas", "estratégia de vendas"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    query_lower = query.lower()

    say("Estrategista Master de Marketing ativada. Qual o objetivo do seu projeto hoje?")
    say("Posso ajudar com: 1 - Avatar/Público | 2 - Ideias de Marketing | 3 - Gatilhos Psicologia | 4 - Motor de Growth")

    opcao = takeCommand(timeout=15)
    if not opcao or opcao == "none":
        return True

    # Se a query original já trouxer o contexto, usamos ela. Se não, perguntamos.
    if len(query) < 20:
        say("Por favor, descreva brevemente seu produto ou serviço.")
        contexto = takeCommand(timeout=20)
    else:
        contexto = query

    say("Processando inteligência de mercado e desenhando sua estratégia...")

    if client and model:
        prompt_base = f"Você é Laura, a Estrategista Master de Marketing. Contexto: {contexto}\n\n"
        
        if "1" in opcao or "público" in opcao or "avatar" in opcao:
            prompt = prompt_base + "Crie um dossiê do AVATAR IDEAL: Nome, idade, dores (o que tira o sono), desejos, objeções de compra e mapa de empatia."
        elif "2" in opcao or "ideia" in opcao:
            prompt = prompt_base + "Gere 5 ideias disruptivas de marketing para este projeto, focando em baixo custo e alto impacto (Growth Hacking)."
        elif "3" in opcao or "gatilho" in opcao or "psicologia" in opcao:
            prompt = prompt_base + "Analise quais os 5 gatilhos mentais mais poderosos para converter este público e como aplicá-los na copy."
        elif "4" in opcao or "growth" in opcao or "crescimento" in opcao:
            prompt = prompt_base + "Desenhe um Motor de Crescimento (Growth Engine): Funil (AARRR), canais de aquisição e métricas chave."
        else:
            prompt = prompt_base + "Faça uma análise estratégica completa unindo Público, Ideias, Psicologia e Growth."

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            resultado = response.choices[0].message.content
            say(resultado)
            
            # SALVAR NO SUPABASE
            from core.database_manager import db
            if "1" in opcao or "público" in opcao or "avatar" in opcao:
                db.save_analysis("personas", {"context": contexto, "persona_data": resultado})
            else:
                db.save_analysis("marketing_analyses", {"url": contexto if "http" in contexto else "N/A", "analysis": resultado, "type": "marketing"})
            
        except Exception as e:
            print(f"Erro ao salvar no DB: {e}")
            say("Erro ao acessar o módulo de estratégia ou banco de dados.")
            
    return True
