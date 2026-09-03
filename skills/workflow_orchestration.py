import time

KEYWORDS = [
    "fluxo de trabalho", "orquestrar", "sequência condicional",
    "workflow", "processo automatizado", "orquestração", "fluxo automatizado",
    "automatizar meu processo", "criar um fluxo", "sequência inteligente",
    "se acontecer", "quando acontecer"
]

# Fluxos pré-definidos conhecidos pela Laura
FLUXOS = {
    "publicação_conteúdo": {
        "nome": "Publicação de Conteúdo",
        "etapas": [
            {"acao": "Pesquisar palavras-chave relevantes para o tema", "tipo": "ia"},
            {"acao": "Gerar estrutura de tópicos do artigo (H1, H2, H3)", "tipo": "ia"},
            {"acao": "Redigir meta description e title tag otimizados para SEO", "tipo": "ia"},
            {"acao": "Sugerir imagens e alt texts", "tipo": "ia"},
            {"acao": "Criar checklist final de publicação", "tipo": "ia"},
        ]
    },
    "campanha_marketing": {
        "nome": "Campanha de Marketing",
        "etapas": [
            {"acao": "Definir objetivo e KPIs da campanha", "tipo": "ia"},
            {"acao": "Identificar público-alvo e persona", "tipo": "ia"},
            {"acao": "Criar mensagem principal (headline + copy)", "tipo": "ia"},
            {"acao": "Sugerir canais de distribuição prioritários", "tipo": "ia"},
            {"acao": "Montar calendário de execução", "tipo": "ia"},
        ]
    }
}

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    query_lower = query.lower()

    # Detectar fluxo pré-definido
    fluxo_ativo = None
    if any(k in query_lower for k in ["conteúdo", "artigo", "post", "publicar"]):
        fluxo_ativo = FLUXOS["publicação_conteúdo"]
    elif any(k in query_lower for k in ["campanha", "marketing", "anúncio", "ads"]):
        fluxo_ativo = FLUXOS["campanha_marketing"]

    if fluxo_ativo:
        say(f"Fluxo '{fluxo_ativo['nome']}' identificado. Sobre qual tema ou produto devo aplicar esse fluxo?")
        tema = takeCommand(timeout=12, phrase_time_limit=20)
        if not tema or tema == "none":
            say("Tema não capturado. Tente novamente.")
            return True

        say(f"Iniciando orquestração do fluxo '{fluxo_ativo['nome']}' para o tema: {tema}. Processando {len(fluxo_ativo['etapas'])} etapas...")

        if client and model:
            etapas_txt = "\n".join([f"{i+1}. {e['acao']}" for i, e in enumerate(fluxo_ativo["etapas"])])
            prompt = (
                f"Você é Laura, uma IA orquestradora de workflows profissionais.\n"
                f"Execute o fluxo de trabalho '{fluxo_ativo['nome']}' para o tema: '{tema}'\n\n"
                f"ETAPAS DO FLUXO:\n{etapas_txt}\n\n"
                f"Para cada etapa, entregue o resultado real e concreto.\n"
                f"Seja detalhada e prática. Use formatação clara com numeração.\n"
                f"Comece com: 'Senhor, iniciando execução do workflow. Resultados de cada etapa:'"
            )
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                say(response.choices[0].message.content)
            except Exception as e:
                say("Erro ao executar o fluxo de trabalho.")
                if context and "log_system_error" in context:
                    context["log_system_error"]("Workflow Orchestration", e)
        return True

    # Modo genérico: Laura cria um workflow personalizado
    say("Modo de orquestração genérico ativado. Descreva o processo que deseja automatizar.")
    processo = takeCommand(timeout=15, phrase_time_limit=30)
    if not processo or processo == "none":
        say("Descrição não capturada. Tente novamente.")
        return True

    say("Mapeando o processo e criando o workflow otimizado...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em orquestração de workflows.\n"
            f"O usuário quer automatizar o seguinte processo:\n'{processo}'\n\n"
            f"Crie um workflow estruturado com:\n"
            f"1. Nome do workflow\n"
            f"2. Gatilho (o que inicia o fluxo)\n"
            f"3. Etapas em sequência (com condições se necessário: 'SE X, ENTÃO Y, SENÃO Z')\n"
            f"4. Resultado esperado\n"
            f"5. Possíveis pontos de falha e contingências\n\n"
            f"Comece com: 'Senhor, mapeei o seguinte workflow:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say("Falha ao criar o workflow.")
            if context and "log_system_error" in context:
                context["log_system_error"]("Workflow Orchestration", e)

    return True
