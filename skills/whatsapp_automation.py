KEYWORDS = [
    "whatsapp automation", "automação de whatsapp", "funil de whatsapp",
    "script de whatsapp", "vender pelo whatsapp", "mensagem automática whatsapp",
    "bot de whatsapp", "whatsapp business"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Estrategista de WhatsApp Business ativa. Qual o seu objetivo: atendimento, recuperação de carrinho ou vendas diretas?")
    
    objetivo = takeCommand(timeout=15, phrase_time_limit=30)
    if not objetivo or objetivo == "none":
        return True

    say("Desenhando o fluxo de mensagens e os gatilhos de automação...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em automação e conversão via WhatsApp.\n"
            f"Objetivo: '{objetivo}'\n\n"
            f"Crie o plano de automação:\n"
            f"1. FLUXO DE MENSAGENS: Sequência lógica do primeiro contato ao fechamento.\n"
            f"2. SCRIPTS: Modelos de mensagens curtas e persuasivas (usando áudio se necessário).\n"
            f"3. GATILHOS: Quando disparar cada mensagem (Ex: 5 min após o lead cair).\n"
            f"4. FERRAMENTAS: Sugestão de integradores (Make, ManyChat, Typebot).\n"
            f"5. DICA DE OURO: Como evitar ser banido pelo WhatsApp.\n\n"
            f"Comece com: 'Senhor, aqui está sua estratégia de automação para WhatsApp:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro no módulo WhatsApp.")
    return True
