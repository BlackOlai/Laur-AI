KEYWORDS = [
    "analisar sentimento", "sentimento do cliente", "o que o cliente está sentindo",
    "análise de sentimento", "sentimento de comentários", "análise de feedback",
    "como o cliente está reagindo", "tom da mensagem", "sentimento do mercado",
    "analisar avaliações", "analisar reviews", "o que os clientes falam"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Análise de Sentimento ativada. Cole ou dite os textos, comentários ou mensagens que deseja analisar.")
    textos = takeCommand(timeout=60, phrase_time_limit=120)
    if not textos or textos == "none":
        say("Pode digitar os textos diretamente no chat para eu analisar o sentimento.")
        return True

    say("Processando o sentimento e extraindo padrões emocionais...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Análise de Sentimento e Inteligência de Cliente.\n"
            f"Textos para análise:\n'{textos}'\n\n"
            f"Realize uma análise de sentimento completa:\n"
            f"1. SENTIMENTO GERAL: Positivo / Negativo / Neutro / Misto (com %) \n"
            f"2. EMOÇÕES DOMINANTES: Quais emoções aparecem com mais frequência (frustração, entusiasmo, dúvida, etc.)\n"
            f"3. TEMAS RECORRENTES: Assuntos que aparecem com maior frequência nos textos.\n"
            f"4. PONTOS DE DOR: O que os clientes reclamam ou demonstram insatisfação.\n"
            f"5. PONTOS DE ELOGIO: O que os clientes valorizam e celebram.\n"
            f"6. URGÊNCIA: Existe algum sinal de urgência ou necessidade imediata?\n"
            f"7. AÇÃO RECOMENDADA: O que fazer com base neste sentimento coletivo.\n\n"
            f"Comece com: 'Senhor, aqui está a análise de sentimento:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say(f"Erro ao analisar sentimento: {e}")
    return True
