KEYWORDS = [
    "prever cancelamento", "risco de churn", "churn prediction", "cliente vai cancelar",
    "perda de cliente", "retenção de clientes", "cliente em risco",
    "analisar churn", "probabilidade de cancelamento", "cliente sumiu"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Análise de Churn ativada. Me passe os dados dos seus clientes: tempo de contrato, última interação, reclamações recentes e histórico de pagamento.")
    dados_clientes = takeCommand(timeout=40, phrase_time_limit=80)
    if not dados_clientes or dados_clientes == "none":
        say("Preciso de dados sobre seus clientes para prever o risco de cancelamento.")
        return True

    say("Calculando risco de churn e estratégias de retenção para cada cliente...")

    if client and model:
        import datetime
        prompt = (
            f"Você é Laura, especialista em Customer Success e Previsão de Churn.\n"
            f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}\n"
            f"Dados dos clientes: '{dados_clientes}'\n\n"
            f"Para cada cliente identificado, analise e entregue:\n"
            f"1. NOME/EMPRESA do cliente\n"
            f"2. RISCO DE CHURN: Baixo / Médio / Alto / Crítico\n"
            f"3. SINAIS DE ALERTA: Comportamentos que indicam intenção de cancelar\n"
            f"4. MOTIVO PROVÁVEL: Por que este cliente pode estar pensando em cancelar\n"
            f"5. PLANO DE RETENÇÃO: Ação específica para resgatar este cliente (ligação, oferta, reunião, etc.)\n"
            f"6. PRAZO: Quanto tempo temos antes de perdê-lo definitivamente\n\n"
            f"No final, liste os 3 clientes mais urgentes para contato imediato.\n"
            f"Comece com: 'Senhor, aqui está a análise de risco dos seus clientes:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say(f"Erro ao analisar churn: {e}")
    return True
