KEYWORDS = [
    "seo master", "especialista seo", "auditoria seo", "plano seo",
    "canibalização seo", "auditar conteúdo", "atualizar conteúdo",
    "palavras-chave", "ranking google", "posicionamento google",
    "seo onpage", "seo técnico", "backlinks"
]

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    say("Consultoria Master de SEO ativada. Qual o domínio ou página que vamos analisar?")
    
    contexto = takeCommand(timeout=20)
    if not contexto or contexto == "none":
        return True

    say("O que você precisa hoje? 1 - Plano SEO Completo | 2 - Auditoria de Conteúdo | 3 - Checar Canibalização | 4 - Sugestão de Atualização")

    opcao = takeCommand(timeout=15)
    if not opcao or opcao == "none":
        return True

    say("Rastreando algoritmos e analisando fatores de ranqueamento...")

    if client and model:
        prompt_base = f"Você é Laura, Especialista Sênior em SEO. Contexto: {contexto}\n\n"
        
        if "1" in opcao or "plano" in opcao:
            prompt = prompt_base + "Crie um Plano de SEO de 3 meses, com foco em Palavras-chave, Autoridade e SEO Técnico."
        elif "2" in opcao or "auditoria" in opcao:
            prompt = prompt_base + "Faça uma auditoria de conteúdo da página citada. Avalie Títulos, Metas, H1-H3 e densidade de palavras-chave."
        elif "3" in opcao or "canibalização" in opcao:
            prompt = prompt_base + "Analise o risco de canibalização de palavras-chave e como consolidar páginas para dominar o Google."
        elif "4" in opcao or "atualização" in opcao or "refresh" in opcao:
            prompt = prompt_base + "Dê sugestões práticas de como atualizar e melhorar conteúdos antigos para recuperar posições no ranking."
        else:
            prompt = prompt_base + "Realize uma análise técnica completa de SEO."

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            resultado = response.choices[0].message.content
            say(resultado)
            
            # SALVAR NO SUPABASE
            from core.database_manager import db
            db.save_analysis("marketing_analyses", {
                "url": contexto if "http" in contexto else "N/A", 
                "analysis": resultado, 
                "type": "seo"
            })
            
        except Exception as e:
            print(f"Erro ao salvar no DB: {e}")
            say("Erro ao acessar o módulo de SEO ou banco de dados.")
            
    return True
