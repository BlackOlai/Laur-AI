KEYWORDS = [
    "qualificar lead", "roteiro de qualificação", "script de qualificação",
    "perguntas para lead", "fit do lead", "qualificação de lead",
    "lead tem fit", "avaliar lead", "filtrar lead", "pré-venda"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Modo Qualificação de Leads ativado. Qual é o seu produto ou serviço e quem é o cliente ideal?")
    produto = takeCommand(timeout=25, phrase_time_limit=50)
    if not produto or produto == "none":
        return True

    say("Gerando roteiro de qualificação personalizado...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Pré-Vendas e Qualificação de Leads (SDR/BDR).\n"
            f"Produto/Serviço: '{produto}'\n\n"
            f"Crie um ROTEIRO COMPLETO de qualificação usando o framework BANT + dores:\n"
            f"1. ABERTURA: Como iniciar a conversa sem soar como vendedor.\n"
            f"2. BUDGET (Orçamento): 3 perguntas para descobrir se tem budget sem perguntar diretamente.\n"
            f"3. AUTHORITY (Autoridade): Como identificar se fala com o tomador de decisão.\n"
            f"4. NEED (Necessidade): 5 perguntas abertas para descobrir a dor real.\n"
            f"5. TIMELINE (Urgência): Como medir o nível de urgência do lead.\n"
            f"6. SCORE: Critérios para pontuar o lead de 1 a 10 (10 = pronto para comprar).\n"
            f"7. PRÓXIMO PASSO: O que fazer com lead quente vs. lead frio.\n\n"
            f"Seja prático e direto. Comece com: 'Senhor, aqui está seu roteiro de qualificação:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say(f"Erro ao gerar roteiro: {e}")
    return True
