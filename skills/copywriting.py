KEYWORDS = [
    "copywriting", "escrever copy", "texto persuasivo", "página de vendas",
    "carta de vendas", "anúncio persuasivo", "headline", "chamada para ação",
    "cta", "copy para email", "venda pelo texto", "copywriter"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    if len(query) > 50:
        objetivo = query
    else:
        say("Modo Copywriter ativado. Para qual produto ou serviço vamos escrever e qual o objetivo?")
        objetivo = takeCommand(timeout=15, phrase_time_limit=30)
        if not objetivo or objetivo == "none":
            return True

    say("Afiando a pena e estruturando a narrativa persuasiva...")

    if client and model:
        prompt = (
            f"Você é Laura, Copywriter de resposta direta nível A.\n"
            f"O objetivo é: '{objetivo}'\n\n"
            f"Entregue:\n"
            f"1. 5 Headlines matadoras (variando entre curiosidade, benefício e medo).\n"
            f"2. Uma Lead (introdução) que prenda a atenção nos primeiros segundos.\n"
            f"3. O corpo do texto usando a estrutura AIDA (Atenção, Interesse, Desejo, Ação).\n"
            f"4. 3 variações de CTA (Call to Action).\n\n"
            f"Use técnicas de storytelling e foque nos benefícios, não nas características.\n"
            f"Comece com: 'Senhor, aqui está sua copy de alta conversão:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            say(response.choices[0].message.content)
        except Exception:
            say("Erro ao gerar copy.")
    return True
