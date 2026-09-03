KEYWORDS = [
    "sales automator", "automação de vendas", "script de vendas",
    "cold email", "follow up", "proposta comercial", "abordagem de vendas",
    "quebra de objeções", "fechamento de vendas", "pitch de vendas",
    "sequência de email", "cadência de email", "sequência de e-mail",
    "cadência de e-mail", "fluxo de email", "automatizar emails"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    # Detecta se é pedido de sequência de e-mails
    seq_keywords = ["sequência", "cadência", "fluxo de email", "sequencia", "e-mail em etapas", "automatizar emails"]
    is_sequence = any(k in query.lower() for k in seq_keywords)

    if is_sequence:
        say("Modo Sequência de E-mails ativado. Para qual produto ou serviço e qual o perfil do lead?")
        produto = takeCommand(timeout=20, phrase_time_limit=40)
        if not produto or produto == "none":
            return True

        say("Estruturando sua cadência de e-mails de alta conversão...")
        if client and model:
            prompt = (
                f"Você é Laura, especialista em Inside Sales e Email Marketing.\n"
                f"Produto/Serviço: '{produto}'\n\n"
                f"Crie uma SEQUÊNCIA COMPLETA de 5 e-mails para nutrição e conversão de leads:\n"
                f"EMAIL 1 (Dia 1 - Prospecção): Assunto intrigante + apresentação de valor sem vender.\n"
                f"EMAIL 2 (Dia 3 - Interesse): Case de sucesso ou dado impactante + CTA suave.\n"
                f"EMAIL 3 (Dia 7 - Desejo): Benefício principal + prova social + urgência leve.\n"
                f"EMAIL 4 (Dia 12 - Decisão): Oferta direta + quebra de objeção principal + CTA claro.\n"
                f"EMAIL 5 (Dia 20 - Breakup): Último contato empático + abertura de canal futuro.\n\n"
                f"Para cada e-mail, entregue: ASSUNTO | CORPO | CTA\n"
                f"Comece com: 'Senhor, aqui está sua cadência de conversão:'"
            )
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                say(response.choices[0].message.content)
            except Exception:
                say("Erro ao gerar sequência de e-mails.")
        return True

    
    venda = takeCommand(timeout=20, phrase_time_limit=40)
    if not venda or venda == "none":
        return True

    say("Desenhando o funil de vendas e criando as peças de abordagem...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Inside Sales e Automação Comercial.\n"
            f"Contexto da venda: '{venda}'\n\n"
            f"Entregue um kit de vendas completo:\n"
            f"1. COLD EMAIL: Uma abordagem inicial curta e intrigante.\n"
            f"2. FOLLOW-UP 1 e 2: Mensagens de acompanhamento que geram valor.\n"
            f"3. PITCH DE ELEVADOR: Como explicar o valor em 30 segundos.\n"
            f"4. QUEBRA DE OBJEÇÕES: Liste as 3 principais desculpas do cliente e como rebatê-las.\n"
            f"5. SCRIPT DE FECHAMENTO: Como conduzir o cliente para o 'sim'.\n\n"
            f"Foque em ser consultivo, não empurrador de produto. Comece com: 'Senhor, aqui está o seu arsenal de vendas:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao gerar kit de vendas.")
    return True
