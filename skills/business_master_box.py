import json
import os

KEYWORDS = ["modo caixa", "análise profunda", "estratégia personalizada", "resolver problema", "executar passo a passo"]

def execute(query, say, takeCommand, context=None):
    client = context.get("client")
    model = context.get("model_to_use")
    
    say("Ativando Modo Caixa. Vou processar sua solicitação em etapas para garantir máxima precisão.")
    
    # Carregar contexto do negócio
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_path = os.path.join(BASE_DIR, "profile.json")
    profile_info = "Contexto não definido."
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_info = f.read()

    # Definir o fluxo da "Caixa"
    prompt_box = f"""
    Você está no MODO CAIXA (Execução de Alta Performance).
    Sua tarefa é resolver: "{query}"
    
    CONTEXTO DO NEGÓCIO:
    {profile_info}
    
    REGRAS DA CAIXA:
    1. Não responda imediatamente. 
    2. Passo 1: Analise o problema sob a ótica do negócio acima.
    3. Passo 2: Busque a solução técnica ou estratégica.
    4. Passo 3: Filtre a solução para remover qualquer generalismo ou 'enchimento'.
    5. Passo 4: Formate a resposta final como um plano de ação direto.

    Responda seguindo rigorosamente esses passos. No final, dê a 'Entrega de Valor'.
    Lembre-se: NÃO AGRADE e NÃO SEJA GENÉRICO.
    """

    try:
        say("Passo 1 e 2: Analisando contexto e buscando informações...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Você é um executor de elite."}, {"role": "user", "content": prompt_box}]
        )
        final_answer = response.choices[0].message.content
        
        say("Passo 3 e 4: Filtrando parâmetros e formatando plano de ação.")
        say(final_answer)
        
    except Exception as e:
        say("Erro ao processar na caixa.")
        if context and "log_system_error" in context:
            context["log_system_error"]("Business Box Skill", e)
            
    return True
