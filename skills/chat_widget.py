KEYWORDS = [
    "chat widget", "criar um chat", "chat para site", "sistema de suporte",
    "widget de conversa", "chat flutuante", "botão de chat", "live chat",
    "atendimento online", "dashboard de suporte", "suporte em tempo real"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    say("Especialista em Chat Widgets ativada. Para qual site ou projeto vamos projetar o sistema de suporte?")
    
    projeto = takeCommand(timeout=15, phrase_time_limit=30)
    if not projeto or projeto == "none":
        return True

    say("Analisando requisitos e desenhando a arquitetura do widget de chat...")

    if client and model:
        prompt = (
            f"Você é Laura, especialista em UX/UI e sistemas de comunicação em tempo real.\n"
            f"O usuário quer criar um 'Chat Widget' para o projeto: '{projeto}'\n\n"
            f"Sua tarefa é projetar o sistema completo:\n"
            f"1. DESIGN DO WIDGET: Descreva como deve ser o botão flutuante e a janela de chat (cores, animações, ícones).\n"
            f"2. FRONTEND (HTML/CSS/JS): Forneça um código-base funcional para um widget flutuante moderno (estilo Glassmorphism).\n"
            f"3. BACKEND SUGERIDO: Qual tecnologia usar para as mensagens (Firebase, WebSockets, Supabase) e por quê.\n"
            f"4. DASHBOARD DE ADMIN: O que o atendente precisa ver (lista de chats, status, histórico).\n"
            f"5. DIFERENCIAL: Uma funcionalidade criativa para esse chat (Ex: tradução automática, integração com IA, etc).\n\n"
            f"Seja técnico e prático. Comece com: 'Senhor, projetei o seguinte sistema de chat para seu site:'"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            projeto_final = response.choices[0].message.content
            say(projeto_final)

            # Oferecer salvar o código/projeto
            say("Deseja que eu salve esta especificação técnica e o código-base em um arquivo?")
            confirmacao = takeCommand(timeout=8, phrase_time_limit=8)
            if confirmacao and any(w in confirmacao.lower() for w in ["sim", "pode", "salva", "salve", "ok"]):
                import os
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                chat_file = os.path.join(BASE_DIR, "chat_widget_project.txt")
                with open(chat_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*60}\n")
                    f.write(f"PROJETO: {projeto}\n")
                    f.write(f"{'='*60}\n")
                    f.write(projeto_final)
                say("Projeto salvo em chat_widget_project.txt na raiz do sistema, senhor.")

        except Exception:
            say("Erro ao projetar o widget de chat.")
    return True
