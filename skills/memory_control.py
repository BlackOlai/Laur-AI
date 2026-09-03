KEYWORDS = ["lembre-se", "lembre se", "memorize", "guarde isso", "anote na memória", "lembrar que", "memorizar que", "guardar que"]

def execute(query, say, takeCommand, context=None):
    query_lower = query.lower()
    
    # Extrair a informação a ser memorizada
    info = query
    for k in KEYWORDS:
        if k in query_lower:
            # Separa pela keyword e pega o que vem depois
            parts = query_lower.split(k, 1)
            if len(parts) > 1 and parts[1].strip():
                # Tenta manter a capitalização original da query
                idx = query_lower.find(k) + len(k)
                info = query[idx:].strip()
                break
                
    # Remove palavras de conexão iniciais
    if info.startswith("que "):
        info = info[4:].strip()
    if info.startswith("de "):
        info = info[3:].strip()
        
    if not info or info.lower() in ["isso", "o que eu disse", "algo"]:
        say("O que você gostaria que eu memorizasse para o longo prazo?")
        info, _ = takeCommand(timeout=15, return_source=True)
        if not info or info == "none":
            say("Tudo bem, não vou memorizar nada agora.")
            return True
            
    # Salvar usando o MemoryManager
    memory_manager = context.get("memory_manager") if context else None
    
    if memory_manager:
        memory_manager.add_memory(info, source="explicit_user_command")
        say("Pronto. Acabei de gravar essa informação na minha memória de longo prazo.")
    else:
        say("Desculpe Olair, o módulo de memória de longo prazo parece estar offline no momento.")
        
    return True
