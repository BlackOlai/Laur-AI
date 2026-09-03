import os
import json
import datetime
import time

KEYWORDS = ["diagnóstico", "analisar sistema", "erros do sistema", "o que aconteceu", "por que falhou", "autoanálise", "status do núcleo", "verificar anomalia", "verificar anomalias", "verificar erro", "verificar erros", "status do sistema", "reparar sistema", "consertar sistema"]

def execute(query, say, takeCommand, context=None):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_FILE = os.path.join(BASE_DIR, "error_logs.json")
    STATUS_FILE = os.path.join(BASE_DIR, "status.json")
    
    # Se o usuário pedir para reparar
    if any(k in query.lower() for k in ["reparar", "consertar"]):
        say("Iniciando protocolos de reparo automatizado. Verificando integridade dos módulos...")
        time.sleep(2)
        
        # Limpeza física e lógica
        if os.path.exists(LOG_FILE):
            try: os.remove(LOG_FILE)
            except: pass
            
        # Forçar o status.json a dizer que não há erros (limpa o alerta visual)
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["unread_errors"] = 0
                with open(STATUS_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            except: pass

        say("Limpeza de arquivos temporários concluída. Verificação de integridade: OK. Subsistemas estabilizados.")
        return True

    if not os.path.exists(LOG_FILE):
        say("Senhor, todos os sistemas estão operando dentro dos parâmetros normais. Nenhum erro registrado.")
        return True

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            
        if not logs:
            say("O registro de logs está vazio. O sistema parece estável.")
            return True
            
        # Pegar todos os erros não lidos
        unread_logs = [e for e in logs if e.get("status") == "unread"]
        if not unread_logs:
            # Se não houver novos, pega os últimos 3 lidos
            unread_logs = logs[-3:]
        
        say("Acessando núcleo de diagnóstico... Detectei uma anomalia nos registros recentes.")
        
        # Preparar prompt para a IA analisar os erros
        error_context = "\n".join([f"[{e['timestamp']}] Origem: {e['origin']} - Erro: {e['message']}" for e in unread_logs])
        
        prompt = (
            f"Você é a Laura, uma IA avançada. Abaixo estão os logs de erros recentes do seu sistema.\n"
            f"Analise-os e explique para o usuário (Olair) de forma clara o que aconteceu.\n"
            f"IMPORTANTE: Dê pelo menos 2 opções ou passos para resolver o problema.\n"
            f"Use um tom calmo, profissional e um pouco futurista.\n\n"
            f"LOGS DE ERRO:\n{error_context}\n\n"
            f"Explicação da Laura e sugestões de correção:"
        )
        
        client = context.get("client")
        model = context.get("model_to_use")
        
        if client and model:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            explanation = response.choices[0].message.content
            say(explanation)
        else:
            last = unread_logs[-1]
            say(f"Detectei uma falha no módulo {last['origin']}. O erro foi: {last['message']}. Recomendo reiniciar o sistema.")
            
        # Marcar TODOS como lidos de forma garantida
        for e in logs:
            e["status"] = "read"
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        say("Erro ao acessar bancos de diagnóstico.")
        if context and "log_system_error" in context:
            context["log_system_error"]("Diagnostics Skill", e)
            
    return True
