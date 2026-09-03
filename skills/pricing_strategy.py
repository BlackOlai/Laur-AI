KEYWORDS = [
    "pricing strategy", "estratégia de preço", "quanto cobrar", "precificação",
    "monetização", "pacotes de serviços", "modelo de assinatura", "upsell",
    "downsell", "order bump", "ticket médio"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Consultora de Precificação ativa. Sobre qual produto ou serviço vamos definir o preço?")
    
    produto = takeCommand(timeout=15, phrase_time_limit=30)
    if not produto or produto == "none":
        return True

    say("Analisando modelos de valor, custos e percepção do mercado...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Precificação e Monetização de Produtos Digitais.\n"
            f"Produto/Serviço: '{produto}'\n\n"
            f"Sua tarefa é desenhar a arquitetura de preços:\n"
            f"1. MODELO: Assinatura, pagamento único ou freemium?\n"
            f"2. ANCORAGEM: Como apresentar o preço para parecer barato.\n"
            f"3. PACOTES (TIERS): Sugira 3 níveis (Ex: Básico, Pro, Enterprise).\n"
            f"4. ESTRATÉGIA DE UPSELL: O que oferecer logo após a primeira compra.\n"
            f"5. LTV (Life Time Value): Como manter o cliente pagando por mais tempo.\n\n"
            f"Comece com: 'Senhor, aqui está a estratégia de precificação recomendada:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro na estratégia de preço.")
    return True
