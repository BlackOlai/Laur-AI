KEYWORDS = [
    "paid ads", "tráfego pago", "anúncios pagos", "facebook ads", "google ads",
    "planejar campanha", "otimizar ads", "gestor de tráfego", "campanha de marketing",
    "ctr", "roas", "cpc", "anunciar no google", "anunciar no facebook"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Gestora de Tráfego Pago ativa. Qual o objetivo da campanha e qual o seu orçamento?")
    
    contexto = takeCommand(timeout=20, phrase_time_limit=40)
    if not contexto or contexto == "none":
        return True

    say("Desenhando a estrutura da campanha e definindo os públicos-alvo...")

    if client and model:
        prompt = (
            f"Você é Laura, gestora de tráfego de alta performance.\n"
            f"Contexto: '{contexto}'\n\n"
            f"Sua tarefa é criar o plano de mídia:\n"
            f"1. ESTRUTURA: Como dividir as campanhas (TOFU, MOFU, BOFU).\n"
            f"2. PÚBLICOS: Sugestões de interesses, lookalikes ou palavras-chave.\n"
            f"3. CRIATIVOS: Que tipo de imagem/vídeo e abordagem usar nos anúncios.\n"
            f"4. MÉTRICAS: Quais KPIs focar para garantir o ROI.\n"
            f"5. OTIMIZAÇÃO: O que fazer se o custo por lead estiver alto.\n\n"
            f"Comece com: 'Senhor, projetei a seguinte estratégia de tráfego pago:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao processar campanha de anúncios.")
    return True
