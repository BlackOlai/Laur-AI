import re
import os
import time
try:
    from skills.info_services import get_full_article, summarize_news, get_youtube_transcript
except ImportError:
    from info_services import get_full_article, summarize_news, get_youtube_transcript

KEYWORDS = ["http://", "https://"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "input.txt")
SKILL_WAIT_FILE = os.path.join(BASE_DIR, "skill_waiting.txt")

def cleanup():
    try:
        os.remove(SKILL_WAIT_FILE)
    except:
        pass

def execute(query, say, takeCommand, context=None):
    
    def wait_for_input(current_url=None, extracted_text=None, step="menu"):
        # Salvar estado para retomada posterior
        import json
        if current_url:
            state = {
                "url": current_url,
                "text": extracted_text[:10000] if extracted_text else "",
                "step": step,
                "timestamp": time.time()
            }
            state_file = os.path.join(BASE_DIR, "last_link_state.json")
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)

        with open(SKILL_WAIT_FILE, "w", encoding="utf-8") as f:
            f.write("link_analyzer")
        
        # A fila do chat (stt._widget_queue) garante que a resposta chegue
        # mesmo enquanto o microfone está aberto. Timeout de 60s para o usuário ter tempo de ler o menu.
        if takeCommand:
            try:
                voice_input = takeCommand(timeout=60) 
                if voice_input and voice_input != "none":
                    try: os.remove(SKILL_WAIT_FILE)
                    except: pass
                    return voice_input.lower()
            except: pass
        
        try: os.remove(SKILL_WAIT_FILE)
        except: pass
        return ""
    
    url_match = re.search(r"https?://\S+", query)
    if not url_match:
        return False
    
    url = url_match.group(0)
    say("Analisando o link.")
    
    
    is_youtube = "youtube.com" in url or "youtu.be" in url
    
    if is_youtube:
        say("Identifiquei que é um vídeo do YouTube. Vou baixar a transcrição para análise...")
        full_text = get_youtube_transcript(url)
    else:
        full_text = get_full_article(url)
        
    if not full_text:
        if is_youtube:
            say("Não consegui extrair as legendas. O vídeo pode não ter transcrição disponível.")
        else:
            say("Não consegui extrair o texto. Deseja que eu abra?")
            ans = wait_for_input()
            if any(w in ans for w in ["sim", "1", "pode", "abre"]):
                import webbrowser
                webbrowser.open(url)
        cleanup()
        return True

    say("Senhor, identifiquei o site com sucesso. O que você deseja que eu faça com ele?")
    say("1 - Resumo: Faço uma síntese rápida dos pontos principais do texto.")
    say("2 - Funções: Analiso e listo todos os recursos e ferramentas que o site oferece.")
    say("3 - Habilidades: Avalio quais dessas funções eu poderia aprender a automatizar.")
    say("4 - Criar Skill: Eu programo uma nova funcionalidade para mim baseada no site agora mesmo.")
    say("5 - Marketing e CRO: Realizo uma auditoria profunda de vendas e conversão.")
    
    choice = wait_for_input(url, full_text, "menu")
    if not choice:
        say("Senhor, como não recebi uma resposta, salvei o progresso desta análise. Basta dizer 'continuar' para retomarmos de onde paramos.")
        return True

    # Opção 1: Resumo breve
    if "1" in choice or "resumo" in choice:
        prompt = f"Faça um resumo breve de 2 parágrafos usando APENAS as informações do texto:\n{full_text[:6000]}"
        say("Gerando resumo...")
        result = summarize_news(full_text, context, custom_prompt=prompt)
        if result:
            say(result)
    
    # Opção 2: Lista todas as funções
    elif "2" in choice or "lista" in choice or "função" in choice:
        prompt = f"Liste TODAS as funcionalidades desta ferramenta:\n{full_text[:7000]}"
        say("Listando funcionalidades...")
        result = summarize_news(full_text, context, custom_prompt=prompt)
        if result:
            say(result)
    
    # Opção 3: Quais podem ser skills + criação inteligente sem duplicatas
    elif "3" in choice or "habilidade" in choice:
        # Passo 1: Lê as KEYWORDS reais de cada skill para inventário preciso
        skills_dir = os.path.join(BASE_DIR, "skills")
        skill_inventory = []
        try:
            for fname in sorted(os.listdir(skills_dir)):
                if not fname.endswith(".py") or fname.startswith("__"):
                    continue
                fpath = os.path.join(skills_dir, fname)
                skill_name = fname[:-3]
                keywords = []
                try:
                    with open(fpath, "r", encoding="utf-8") as sf:
                        content_lines = sf.read()
                    kw_match = re.search(r"KEYWORDS\s*=\s*\[(.*?)\]", content_lines, re.DOTALL)
                    if kw_match:
                        raw_kws = kw_match.group(1)
                        keywords = re.findall(r'"([^"]+)"', raw_kws)
                except: pass
                if keywords:
                    skill_inventory.append(f"{skill_name}: [{', '.join(keywords[:6])}]")
                else:
                    skill_inventory.append(skill_name.replace("_", " "))
        except: pass
        existing_str = "\n".join(skill_inventory)

        # Passo 2: IA analisa o site e identifica habilidades candidatas de forma rigorosa
        prompt_analise = (
            f"Você é um Especialista em Engenharia de Agentes de IA. Analise este site e identifique ATÉ 5 funções técnicas "
            f"específicas que um assistente de IA poderia executar baseado nos serviços oferecidos na página. "
            f"FOCO: Procure por ferramentas, calculadoras, geradores de roteiro, análises preditivas ou automações de fluxo. "
            f"REGRAS:\n"
            f"1. Não sugira coisas genéricas que quase toda IA faz (ex: 'responder perguntas', 'resumir texto').\n"
            f"2. Seja MUITO específico. Em vez de 'Marketing', sugira 'Gerador de Roteiro de Qualificação de Leads'.\n"
            f"3. Ignore o que já temos na lista abaixo.\n\n"
            f"HABILIDADES JÁ INSTALADAS (NÃO SUGIRA ESTAS OU SINÔNIMOS ÓBVIOS):\n{existing_str}\n\n"
            f"TEXTO DO SITE:\n{full_text[:8000]}"
        )
        say("Realizando varredura técnica no site para identificar habilidades de elite...")
        result = summarize_news(full_text, context, custom_prompt=prompt_analise, max_tokens=800)
        
        if not result or len(result.strip()) < 10:
            say("Após uma análise profunda, não identifiquei habilidades técnicas novas que superem as que já possuo neste site.")
        else:
            say("Identifiquei potenciais habilidades de alto nível:")
            say(result)

            # Passo 3: IA filtra de forma ultra-rigorosa (Semântica vs Nome)
            prompt_filtro = (
                f"Compare as HABILIDADES CANDIDATAS com as HABILIDADES JÁ INSTALADAS.\n"
                f"Sua missão é ser um 'Caçador de Inovação'. Só descarte uma habilidade se ela for EXATAMENTE a mesma coisa que já temos.\n"
                f"REGRAS DE OURO:\n"
                f"1. Especialização = Nova. Ex: Se temos 'Vendas', mas a candidata é 'Análise Preditiva de Churn', ela é NOVA.\n"
                f"2. Scripts Específicos = Novos. Ex: Se temos 'Copywriting', mas a candidata é 'Gerador de Roteiro de Qualificação', ela é NOVA.\n"
                f"3. Se houver dúvida, considere como NOVA.\n\n"
                f"LISTA JÁ INSTALADA:\n{existing_str}\n\n"
                f"CANDIDATAS:\n{result}\n\n"
                f"Retorne sua análise no formato:\n"
                f"NOVAS: [lista de nomes separados por vírgula]\n"
                f"REDUNDANTES: [nome da nova] -> [nome da que já existe]\n\n"
                f"Se não houver nenhuma nova, escreva 'NOVAS: NENHUMA'."
            )
            analise_raw = summarize_news("", context, custom_prompt=prompt_filtro, max_tokens=500)
            
            # Processa a resposta da IA
            novas = []
            redundantes_msg = ""
            if analise_raw:
                novas_match = re.search(r"NOVAS:\s*(.*)", analise_raw, re.IGNORECASE)
                if novas_match:
                    novas_str = novas_match.group(1).strip()
                    if "nenhuma" not in novas_str.lower():
                        novas = [s.strip() for s in novas_str.split(",") if s.strip()]
                
                red_match = re.search(r"REDUNDANTES:\s*(.*)", analise_raw, re.IGNORECASE | re.DOTALL)
                if red_match:
                    redundantes_msg = red_match.group(1).strip()

            if not novas:
                if redundantes_msg:
                    say(f"Senhor, analisei as habilidades e elas parecem duplicatas das que já possuo. Veja o que identifiquei: {redundantes_msg}")
                else:
                    say("Senhor, todas as habilidades que identifiquei já existem no meu sistema de forma similar.")
                
                say("Deseja que eu ignore minha análise de segurança e crie uma delas mesmo assim? Se sim, diga o nome da habilidade.")
                confirmacao = wait_for_input(url, full_text, "force_skill_confirm")
                if confirmacao and confirmacao not in ["não", "nao", "não obrigado", "cancelar"]:
                    # Se ele disse um nome ou "sim", tentamos criar a primeira ou a mencionada
                    novas = [confirmacao] if "sim" not in confirmacao else [result.split("\n")[0][:30]]
            
            if novas:
                say(f"Entendido. Posso criar as seguintes habilidades novas: {', '.join(novas)}.")
                say("Deseja que eu crie todas agora? Diga 'sim' para todas, ou o nome de uma específica.")
                
                confirmacao = wait_for_input(url, full_text, "skills_confirm")
                if not confirmacao or any(w in confirmacao for w in ["não", "nao", "agora não", "depois"]):
                    say("Entendido, senhor. As habilidades ficam salvas na análise para quando quiser.")
                else:
                    # Cria todas ou a específica mencionada
                    if any(w in confirmacao for w in ["sim", "todas", "pode", "cria"]):
                        para_criar = novas
                    else:
                        # Filtra pelo nome mencionado
                        para_criar = [n for n in novas if any(word in confirmacao for word in n.lower().split())]
                        if not para_criar:
                            para_criar = novas[:1]  # fallback: cria a primeira

                    from skills.skill_creator import generate_skill_code
                    criadas = []
                    for skill_name in para_criar:
                        say(f"Criando habilidade: {skill_name}...")
                        desc = f"Criar skill chamada '{skill_name}' baseada no site {url}. Contexto: {full_text[:3000]}"
                        code = generate_skill_code(desc, context)
                        if code:
                            safe_name = skill_name.lower().replace(" ", "_").replace("-", "_")
                            file_name = f"skill_{safe_name[:20]}_{os.urandom(2).hex()}.py"
                            file_path = os.path.join(skills_dir, file_name)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(code)
                            criadas.append(skill_name)
                    
                    if criadas:
                        say(f"Criações concluídas! Habilidades novas: {', '.join(criadas)}. Diga 'recarregar habilidades' para ativá-las.")
                    else:
                        say("Não consegui gerar o código para as habilidades desta vez.")
    
    # Opção 4: Criar skill
    elif "4" in choice or "criar" in choice or "skill" in choice:
        say("Qual funcionalidade deseja transformar em habilidade?")
        func_name = wait_for_input()
        if func_name and func_name not in ["não", "nao", "nenhuma", "n"]:
            desc = f"Criar skill '{func_name}' baseado no site: {full_text[:3000]}"
            from skills.skill_creator import generate_skill_code
            code = generate_skill_code(desc, context)
            if code:
                file_name = f"skill_auto_{os.urandom(2).hex()}.py"
                with open(os.path.join("skills", file_name), "w", encoding="utf-8") as f:
                    f.write(code)
                say(f"Habilidade '{func_name}' criada com sucesso. Diga: recarregar.")

    # NOVO: Opção 5 - Auditoria de Marketing & CRO (Fluxo Agêntico)
    elif "5" in choice or "marketing" in choice or "cro" in choice or "estratégia" in choice:
        prompt = f"""Realize uma auditoria profissional de marketing e conversão (CRO) deste site.
        Analise o texto abaixo e responda nos seguintes tópicos:
        1. OBJETIVO E PÚBLICO: Qual o objetivo da página e quem ela quer atingir?
        2. PONTOS FORTES E FRACOS: O que está bom e o que está ruim?
        3. MELHORIAS (DESIGN E COPY): O que mudar na aparência e na escrita para converter mais?
        4. ESTRATÉGIA: Qual a melhor estratégia de marketing para este produto?
        5. IDEIA DE CAMPANHA: Uma sugestão rápida de campanha.

        TEXTO DO SITE:
        {full_text[:8000]}
        """
        say("Iniciando auditoria de marketing e CRO, um momento...")
        result = summarize_news(full_text, context, custom_prompt=prompt, max_tokens=2500)
        if result:
            analysis_file = os.path.join(BASE_DIR, "last_marketing_analysis.json")
            try:
                import json
                with open(analysis_file, "w", encoding="utf-8") as f:
                    json.dump({"url": url, "analysis": result, "timestamp": time.time()}, f, ensure_ascii=False)
            except: pass
            
            say("Auditoria concluída senhor. Aqui estão os pontos principais:")
            say(result)
            
            # MENU DE EXECUÇÃO AGÊNTICA
            say("A análise foi salva. Como deseja prosseguir com as melhorias?")
            say("1 - Copy | 2 - Ads | 3 - Social | 4 - Growth | 5 - Público/Avatar | 6 - DOCX")
            
            exec_choice = wait_for_input(url, full_text, "execution_menu")
            if not exec_choice:
                say("Análise salva, senhor. Estarei aqui se desejar executar as melhorias depois.")
                return True
            
            if "1" in exec_choice or "copy" in exec_choice:
                from skills.copywriting import execute as exec_copy
                say("Acionando módulo de Copywriting com base na análise do site...")
                exec_copy(f"Criar copy otimizada para o site {url} baseada nesta análise: {result[:2000]}", say, takeCommand, context)
            
            elif "2" in exec_choice or "anúncio" in exec_choice or "ads" in exec_choice:
                from skills.paid_ads import execute as exec_ads
                say("Planejando campanha de tráfego pago para este site...")
                exec_ads(f"Planejar anúncios para {url} usando esta estratégia: {result[:2000]}", say, takeCommand, context)
                
            elif "3" in exec_choice or "post" in exec_choice or "social" in exec_choice:
                from skills.social_content import execute as exec_social
                say("Gerando pauta de conteúdo social para este projeto...")
                exec_social(f"Criar estratégia social para o site {url}. Contexto: {result[:2000]}", say, takeCommand, context)

            elif "4" in exec_choice or "growth" in exec_choice:
                from skills.growth_engine import execute as exec_growth
                say("Calculando motor de crescimento para este projeto...")
                exec_growth(f"Desenhar growth engine para {url}. Base: {result[:2000]}", say, takeCommand, context)

            elif "5" in exec_choice or "público" in exec_choice or "avatar" in exec_choice or "persona" in exec_choice:
                from skills.audience_analyzer import execute as exec_audience
                say("Iniciando análise profunda do público-alvo para este site...")
                exec_audience(f"Analisar o público ideal para o site {url} baseado neste contexto: {result[:2000]}", say, takeCommand, context)

            elif "6" in exec_choice or "relatório" in exec_choice or "report" in exec_choice or "word" in exec_choice:
                from skills.report_generator import execute as exec_report
                exec_report(query, say, takeCommand, context)

    else:
        say("Opção inválida ou tempo esgotado.")
    
    say("Deseja abrir o site para conferir?")
    ans = wait_for_input()
    if any(w in ans for w in ["sim", "quero", "pode", "ok"]):
        import webbrowser
        webbrowser.open(url)
    
    cleanup()
    say("Análise de link finalizada, senhor.")
    return True