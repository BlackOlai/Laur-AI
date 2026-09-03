KEYWORDS = [
    "perfil do lead", "perfil da empresa", "pesquisar empresa", "background do lead",
    "informações da empresa", "dados do prospect", "quem é a empresa",
    "detalhar empresa", "levantar dados do cliente", "ficha do lead"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Lead Profiler ativado. Qual é o nome da empresa ou lead que deseja pesquisar?")
    empresa = takeCommand(timeout=20, phrase_time_limit=40)
    if not empresa or empresa == "none":
        return True

    say(f"Levantando perfil completo de {empresa}...")

    if client and model:
        import datetime
        prompt = (
            f"Você é Laura, especialista em Inteligência Comercial e Prospecção B2B.\n"
            f"Empresa/Lead: '{empresa}'\n"
            f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}\n\n"
            f"Gere um PERFIL COMERCIAL COMPLETO baseado no que é possível inferir e no conhecimento público:\n"
            f"1. SOBRE A EMPRESA: Segmento, porte estimado, modelo de negócio, posicionamento.\n"
            f"2. PÚBLICO-ALVO: Para quem essa empresa vende (se for B2B ou B2C).\n"
            f"3. DORES PROVÁVEIS: Quais problemas essa empresa provavelmente enfrenta.\n"
            f"4. OPORTUNIDADE COMERCIAL: Como o GestãoPro / Laura AI poderia ajudá-la.\n"
            f"5. ÂNGULO DE ABORDAGEM: Como iniciar a conversa com este prospect.\n"
            f"6. PERGUNTAS-CHAVE: 5 perguntas para fazer na primeira call com essa empresa.\n"
            f"7. TOMADOR DE DECISÃO PROVÁVEL: Cargo e perfil de quem decide a compra.\n\n"
            f"Comece com: 'Senhor, aqui está o perfil comercial de {empresa}:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception as e:
            say(f"Erro ao gerar perfil: {e}")
    return True
