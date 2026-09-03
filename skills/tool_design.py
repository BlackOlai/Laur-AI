KEYWORDS = [
    "criar uma ferramenta", "desenhar uma skill", "projetar uma função",
    "nova habilidade para você", "planejar ferramenta", "me ajude a criar uma skill",
    "criar uma skill", "nova skill", "nova função para a laura",
    "tool design", "desenhar ferramenta", "projetar skill"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Modo de design de ferramentas ativado. Descreva a funcionalidade que você quer criar para mim.")
    
    descricao = takeCommand(timeout=15, phrase_time_limit=30)
    if not descricao or descricao == "none":
        say("Não captei a descrição. Tente digitar no chat.")
        return True

    say("Analisando a especificação e desenhando a arquitetura da nova ferramenta. Um momento...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em design de skills e ferramentas de IA.\n"
            f"O usuário quer criar a seguinte funcionalidade para você:\n'{descricao}'\n\n"
            f"Crie o plano técnico completo da skill com:\n\n"
            f"1. NOME SUGERIDO: nome do arquivo Python (snake_case.py)\n"
            f"2. PALAVRAS-CHAVE: lista de 8 a 12 frases que ativarão esta skill (em português)\n"
            f"3. ENTRADAS: o que a skill precisa coletar do usuário\n"
            f"4. LÓGICA PRINCIPAL: passo a passo do que a skill faz internamente\n"
            f"5. APIS/LIBS: quais bibliotecas Python ou APIs serão necessárias\n"
            f"6. SAÍDA: o que a Laura responde ao usuário\n"
            f"7. CASOS DE BORDA: o que fazer se algo falhar\n"
            f"8. CÓDIGO BASE: esboço do arquivo Python seguindo o padrão:\n"
            f"   - KEYWORDS = [...]\n"
            f"   - def execute(query, say, takeCommand, context=None):\n\n"
            f"Seja técnico, detalhado e prático. Comece com: 'Senhor, projetei a seguinte ferramenta:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            design = response.choices[0].message.content
            say(design)

            say("Devo salvar esse plano em um arquivo de especificação para você?")
            confirmacao = takeCommand(timeout=8, phrase_time_limit=8)
            if confirmacao and any(w in confirmacao.lower() for w in ["sim", "pode", "salva", "salve", "ok"]):
                import os
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                spec_file = os.path.join(BASE_DIR, "tool_specs.txt")
                with open(spec_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*60}\n")
                    f.write(f"ESPECIFICAÇÃO: {descricao}\n")
                    f.write(f"{'='*60}\n")
                    f.write(design)
                say("Especificação salva em tool_specs.txt na raiz do projeto, senhor.")

        except Exception as e:
            say("Falha ao gerar o design da ferramenta.")
            if context and "log_system_error" in context:
                context["log_system_error"]("Tool Design Skill", e)
    else:
        say("Módulo de inteligência indisponível.")

    return True
