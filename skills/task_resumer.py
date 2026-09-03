import os
import json

KEYWORDS = [
    "continuar", "retomar", "voltar para", "onde paramos", 
    "continuar análise", "retomar análise", "voltar para o site",
    "continuar última tarefa", "retomar última tarefa"
]

def execute(query, say, takeCommand, context=None):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(BASE_DIR, "last_link_state.json")
    
    if not os.path.exists(state_file):
        say("Senhor, não encontrei nenhuma tarefa pendente ou análise recente para retomar.")
        return True

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = data = json.load(f)
        
        url = data.get("url")
        full_text = data.get("text")
        step = data.get("step", "menu")
        
        say(f"Retomando a análise do site: {url}")
        
        # Importar a skill de link_analyzer para re-executar o menu
        from skills.link_analyzer import execute as exec_link
        
        # Criamos uma "query artificial" para o link_analyzer reconhecer a URL
        fake_query = f"analisar {url}"
        
        # Chamamos o link_analyzer passando o contexto já carregado
        # Nota: O link_analyzer precisará ser levemente ajustado para aceitar texto pré-carregado 
        # ou apenas re-rodar e extrair novamente (o Jina Reader é rápido).
        # Para manter simples, vamos re-rodar o link_analyzer.
        
        return exec_link(fake_query, say, takeCommand, context)

    except Exception as e:
        print(f"Erro ao retomar tarefa: {e}")
        say("Houve um erro ao tentar recuperar o estado da última tarefa.")
        
    return True
