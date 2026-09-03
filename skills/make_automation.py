KEYWORDS = [
    "make", "make.com", "integromat", "automação no make", "cenário no make",
    "criar cenário", "planejar automação", "debugar automação", "automação quebrada",
    "erro no make", "modulo do make", "zapier", "webhook", "trigger",
    "otimizar cenário", "blueprint do make", "integração automática",
    "quando alguém preencher", "quando receber um email", "conectar sistemas",
    "automatizar processo make", "fluxo no make"
]

# Módulos mais comuns do Make por categoria — contexto para a IA
MAKE_CONTEXT = """
MÓDULOS MAKE MAIS COMUNS:
- GATILHOS (Watch): Watch emails, Watch forms, Watch rows (Sheets), Webhooks, Schedule
- HTTP/API: HTTP Make a request, HTTP Make Basic Auth, Parse JSON/XML
- FILTROS: Filter (condição para continuar), Router (ramificar fluxo)
- GOOGLE: Google Sheets (Add/Update/Search rows), Gmail, Google Drive, Google Docs, Google Calendar
- COMUNICAÇÃO: Email, WhatsApp Business, Telegram Bot, Slack, Discord
- CRM/MARKETING: HubSpot, Mailchimp, ActiveCampaign, RD Station
- E-COMMERCE: Shopify, WooCommerce, Stripe, Hotmart, Eduzz
- PRODUTIVIDADE: Notion, Trello, Asana, Monday, Airtable
- DADOS: Data Store, JSON, Text Parser, Array Aggregator, Iterator
- IA: OpenAI, Claude (Anthropic), Gemini
- WORDPRESS: WordPress (create post, update post)
- SOCIAL: Instagram Business, Facebook Pages, LinkedIn, YouTube

BOAS PRÁTICAS DO MAKE:
- Use Error Handlers para capturar falhas sem quebrar o cenário
- Filtre dados o mais cedo possível no fluxo para economizar operações
- Use Data Stores para persistir dados entre cenários
- Webhooks são mais eficientes que Polling para gatilhos em tempo real
- Routers permitem ramificar o fluxo com condições
- Aggregators consolidam múltiplos bundles em um único
- Iterators expandem arrays para processar item por item
"""

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    query_lower = query.lower()

    blueprint_data = ""
    # Detectar se há um JSON anexado vindo do processador de arquivos
    if "[ARQUIVO ANEXADO:" in query and (".json" in query_lower or "conteúdo do arquivo" in query_lower):
        say("Identifiquei um arquivo de Blueprint do Make. Iniciando auditoria técnica da estrutura...")
        blueprint_data = query # O conteúdo do arquivo já vem na query pelo widget_launcher
        modo = "auditoria_json"
    
    # Detectar intenção por voz se não houver arquivo
    elif any(k in query_lower for k in ["debugar", "erro no make", "automação quebrada", "não está funcionando", "falhou"]):
        modo = "debug"
        say("Modo de diagnóstico do Make ativado. Descreva o erro que está vendo.")
    elif any(k in query_lower for k in ["otimizar", "melhorar cenário", "reduzir operações"]):
        modo = "otimizar"
        say("Modo de otimização ativado. Descreva seu cenário ou anexe o JSON.")
    elif any(k in query_lower for k in ["criar cenário", "planejar", "blueprint", "novo cenário"]):
        modo = "planejar"
        say("Modo de planejamento ativado. O que deseja automatizar?")
    else:
        modo = "consulta"
        say("Consultora Make ativa. Como posso ajudar com suas automações?")

    # Se não for auditoria de JSON, precisa de descrição por voz
    descricao = ""
    if modo != "auditoria_json":
        descricao = takeCommand(timeout=20, phrase_time_limit=40)
        if not descricao or descricao == "none":
            return True
        say("Analisando padrões e mapeando módulos...")
    else:
        descricao = "Análise técnica de blueprint JSON."

    if client and model:
        prompts = {
            "auditoria_json": (
                f"Você é Laura, Auditora Sênior de Arquitetura no Make.com.\n"
                f"O usuário anexou um Blueprint JSON:\n{blueprint_data[:10000]}\n\n"
                f"Analise a estrutura técnica e responda:\n"
                f"1. MAPA DO FLUXO: Quais módulos principais você identificou e a ordem deles.\n"
                f"2. PONTOS DE FALHA: Onde o cenário pode quebrar e onde faltam 'Error Handlers'.\n"
                f"3. OTIMIZAÇÃO: Módulos que podem ser substituídos ou filtros que podem ser adicionados para poupar operações.\n"
                f"4. DICA PRO: Uma configuração avançada específica para os módulos encontrados no JSON.\n"
                f"Comece com: 'Senhor, analisei a estrutura do seu JSON e aqui está a auditoria técnica:'"
            ),
            "debug": (
                f"Você é Laura, especialista em Make.com.\n"
                f"O problema relatado é: '{descricao}'\n\n"
                f"Forneça: Causa provável, como verificar no log do Make e a solução passo a passo."
            ),
            "otimizar": (
                f"Você é Laura, especialista em eficiência no Make.\n"
                f"Cenário: '{descricao}'\n\n"
                f"Sugira como reduzir o consumo de operações e melhorar a velocidade de execução."
            ),
            "planejar": (
                f"Você é Laura, arquiteta de automações.\n"
                f"Objetivo: '{descricao}'\n\n"
                f"Crie o blueprint sugerido: Gatilho -> Filtros -> Módulos de Ação -> Tratamento de Erros."
            ),
            "consulta": (
                f"Você é Laura, consultora de automações Make.\n"
                f"Pergunta: '{descricao}'\n\n"
                f"Responda de forma prática e estratégica."
            )
        }

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompts[modo]}]
            )
            resultado = response.choices[0].message.content
            say(resultado)

            if modo in ["auditoria_json", "planejar"]:
                say("Deseja salvar esta análise no seu histórico de blueprints?")
                confirm = takeCommand(timeout=8)
                if confirm and any(w in confirm.lower() for w in ["sim", "pode", "salva", "ok"]):
                    import datetime
                    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    with open(os.path.join(BASE_DIR, "make_blueprints.txt"), "a", encoding="utf-8") as f:
                        f.write(f"\n\n[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}] AUDITORIA TÉCNICA\n")
                        f.write(resultado)
                    say("Análise técnica salva com sucesso.")

        except Exception as e:
            say("Erro ao processar auditoria do Make.")
            print(f"Erro Make: {e}")
            
    return True
