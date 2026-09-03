KEYWORDS = [
    "pontuar lead", "score de lead", "lead scoring", "priorizar leads",
    "classificar leads", "lead mais quente", "rankear leads",
    "qual lead priorizar", "probabilidade de fechamento", "lead score"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Lead Scoring ativado. Me passe os dados dos seus leads: nome, cargo, empresa, interações recentes e estágio no funil.")
    dados_leads = takeCommand(timeout=40, phrase_time_limit=80)
    if not dados_leads or dados_leads == "none":
        say("Tudo bem. Para pontuar os leads, precisarei dos dados de cada um.")
        return True

    say("Analisando e pontuando seus leads por probabilidade de fechamento...")

    if client and model:
        import datetime
        prompt = (
            f"Você é Laura, especialista em Revenue Intelligence e Lead Scoring preditivo.\n"
            f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}\n"
            f"Dados dos leads: '{dados_leads}'\n\n"
            f"Para cada lead identificado, entregue:\n"
            f"1. NOME/EMPRESA do lead\n"
            f"2. SCORE (0-100): Pontuação de probabilidade de fechamento\n"
            f"3. NÍVEL: Frio (<40), Morno (40-70), Quente (>70), Pronto para Fechar (>90)\n"
            f"4. FATORES POSITIVOS: O que aumenta a pontuação\n"
            f"5. FATORES DE RISCO: O que pode travar o fechamento\n"
            f"6. AÇÃO RECOMENDADA: O que fazer com este lead agora\n\n"
            f"No final, ordene os leads do mais quente para o mais frio.\n"
            f"Comece com: 'Senhor, aqui está o ranking dos seus leads:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say(f"Erro ao calcular lead score: {e}")
    return True
