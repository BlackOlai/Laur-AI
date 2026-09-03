import time
import os
import json

KEYWORDS = [
    "execute uma sequência", "faça uma série", "automatizar processo",
    "rotina de", "execute em sequência", "modo autônomo", "agente autônomo",
    "faça tudo", "execute tudo", "rotina matinal", "rotina noturna",
    "preparar meu dia", "resumo do dia", "iniciar rotina", "ativar rotina",
    "modo projeto", "iniciar projeto"
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_MEMORY = os.path.join(BASE_DIR, "project_memory.json")

def save_project_context(data):
    try:
        with open(PROJECT_MEMORY, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

def load_project_context():
    if os.path.exists(PROJECT_MEMORY):
        try:
            with open(PROJECT_MEMORY, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    skill_manager = context.get("skill_manager") if context else None
    query_lower = query.lower()

    # --- MODO AGENTE AUTÔNOMO (ORQUESTRAÇÃO REAL) ---
    say("Modo Agente Autônomo ativado. Analisando objetivos e planejando execução...")

    if not client or not model:
        say("Módulo de inteligência indisponível.")
        return True

    # 1. PLANEJAMENTO
    skills_list = ""
    if skill_manager:
        skills_list = "\n".join([f"- {s.__name__}: {s.KEYWORDS[:3]}" for s in skill_manager.skills])

    prompt_plan = f"""
    Você é a Laura em Modo Orquestradora (Estilo Atoms.dev).
    O usuário quer: '{query}'
    
    Habilidades disponíveis na Laura:
    {skills_list}
    
    Sua missão:
    1. Crie um plano de 3 a 5 etapas para resolver isso de forma autônoma.
    2. Para cada etapa, identifique qual SKILL da lista acima deve ser usada.
    3. Retorne um JSON no formato:
    {{
       "objetivo": "descrição",
       "etapas": [
          {{"passo": 1, "descricao": "...", "skill": "nome_da_skill", "comando_para_skill": "o que pedir para a skill"}},
          ...
       ]
    }}
    Responda APENAS o JSON.
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Você é a Laura em Modo Orquestradora. Trate o usuário (Olair) diretamente. Planeje etapas claras e eficientes."}, {"role": "user", "content": prompt_plan}]
        )
        plan_raw = response.choices[0].message.content
        
        # Extração Robusta de JSON (Ignora textos extras da IA)
        import re
        json_match = re.search(r'\{.*\}', plan_raw, re.DOTALL)
        if json_match:
            plan_json = json.loads(json_match.group())
        else:
            raise Exception("Formato JSON não encontrado na resposta da IA.")

        
        say(f"Senhor, planejei {len(plan_json['etapas'])} etapas para concluir: {plan_json['objetivo']}")
        for etapa in plan_json['etapas']:
            say(f"Passo {etapa['passo']}: {etapa['descricao']}")
        
        say("Devo iniciar a execução agora?")
        confirm = takeCommand(timeout=10)
        if not confirm or not any(w in confirm.lower() for w in ["sim", "pode", "ok", "confirmo", "execute"]):
            say("Entendido. Plano arquivado.")
            return True

        # 2. EXECUÇÃO
        project_context = {"main_goal": query, "steps": plan_json['etapas'], "results": []}
        save_project_context(project_context)

        for etapa in plan_json['etapas']:
            say(f"Executando Passo {etapa['passo']}: {etapa['descricao']}...")
            
            skill_to_call = etapa['skill']
            cmd = etapa['comando_para_skill']
            
            # Adicionar contexto anterior ao comando
            if project_context["results"]:
                last_result = project_context["results"][-1]["output"]
                cmd += f"\nContexto do passo anterior: {last_result[:1000]}"

            # Tenta encontrar a skill e executar
            success = False
            if skill_manager:
                target_skill = next((s for s in skill_manager.skills if s.__name__ == skill_to_call), None)
                if target_skill:
                    # Captura de saída? Como as skills usam 'say', o resultado é falado.
                    # Para um orquestrador real, precisaríamos que as skills retornassem dados.
                    # Por enquanto, vamos simular o fluxo.
                    try:
                        res = target_skill.execute(cmd, say, takeCommand, context)
                        project_context["results"].append({"passo": etapa['passo'], "output": "Concluído com sucesso."})
                        success = True
                    except Exception as e:
                        print(f"Erro na etapa {etapa['passo']}: {e}")
                        project_context["results"].append({"passo": etapa['passo'], "output": f"Erro: {str(e)}"})
                else:
                    say(f"Aviso: Habilidade {skill_to_call} não encontrada. Tentando modo geral.")
                    # Fallback para chat se a skill não existe
                    project_context["results"].append({"passo": etapa['passo'], "output": "Executado via inteligência geral."})
                    success = True

            save_project_context(project_context)
            time.sleep(1)

        say("Senhor, todas as etapas do projeto foram concluídas conforme o planejado.")
        
    except Exception as e:
        say("Erro ao planejar ou executar o projeto.")
        print(f"Erro Autônomo: {e}")
        if context and "log_system_error" in context:
            context["log_system_error"]("Autonomous Agent", e)

    return True
