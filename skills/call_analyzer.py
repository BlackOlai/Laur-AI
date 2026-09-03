KEYWORDS = [
    "analisar ligação", "transcrever ligação", "analisar chamada", "transcrever chamada",
    "o que aconteceu na ligação", "resumo da ligação", "análise de chamada",
    "objeções da ligação", "feedback da ligação", "analisar conversa de vendas"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Análise de Ligação ativada. Cole ou dite o conteúdo da ligação ou transcrição que deseja analisar.")
    transcricao = takeCommand(timeout=60, phrase_time_limit=120)
    if not transcricao or transcricao == "none":
        say("Não recebi o conteúdo da ligação. Pode digitar no chat e eu analiso.")
        return True

    say("Analisando a ligação de vendas e extraindo os insights principais...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em Coaching de Vendas e Análise de Conversas Comerciais.\n"
            f"Transcrição/Conteúdo da ligação:\n'{transcricao}'\n\n"
            f"Faça uma análise completa da ligação de vendas:\n"
            f"1. RESUMO EXECUTIVO: O que aconteceu na ligação em 3 frases.\n"
            f"2. SENTIMENTO DO CLIENTE: Positivo / Neutro / Negativo e por quê.\n"
            f"3. OBJEÇÕES LEVANTADAS: Liste cada objeção e como o vendedor respondeu.\n"
            f"4. MOMENTOS CRÍTICOS: Pontos da conversa que definiram o resultado.\n"
            f"5. PONTOS FORTES DO VENDEDOR: O que ele fez bem.\n"
            f"6. PONTOS DE MELHORIA: O que poderia ter sido feito diferente.\n"
            f"7. PRÓXIMO PASSO IDEAL: Qual deveria ser o follow-up ideal após esta ligação.\n"
            f"8. PROBABILIDADE DE FECHAMENTO: Estimativa em % com justificativa.\n\n"
            f"Comece com: 'Senhor, aqui está a análise da sua ligação:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say(f"Erro ao analisar ligação: {e}")
    return True
