KEYWORDS = [
    "competitive landscape", "panorama competitivo", "mapeamento de mercado",
    "diferenciação", "vantagem competitiva", "estratégia de mercado",
    "onde competir", "como vencer", "matriz competitiva"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Análise de Panorama Competitivo ativa. Qual o seu setor ou nicho de atuação?")
    
    nicho = takeCommand(timeout=15, phrase_time_limit=30)
    if not nicho or nicho == "none":
        return True

    say("Mapeando o ecossistema e buscando diferenciais competitivos...")

    if client and model:
        prompt = (
            f"Você é Laura, estrategista de mercado nível Senior.\n"
            f"O nicho é: '{nicho}'\n\n"
            f"Sua tarefa é desenhar o panorama competitivo:\n"
            f"1. SEGMENTAÇÃO: Como os players estão divididos.\n"
            f"2. BARREIRAS DE ENTRADA: O que dificulta novos competidores.\n"
            f"3. FATORES CRÍTICOS DE SUCESSO: O que é obrigatório para vencer nesse nicho.\n"
            f"4. ESTRATÉGIA DE DIFERENCIAÇÃO: Como o usuário pode ser único (Oceano Azul).\n"
            f"5. TENDÊNCIAS: Para onde o mercado está indo.\n\n"
            f"Comece com: 'Senhor, mapeei o seguinte panorama competitivo:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao mapear mercado.")
    return True
