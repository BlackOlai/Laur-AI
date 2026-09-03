import os
from dotenv import load_dotenv

def validate_config():
    """
    Valida as configurações do ambiente (.env).
    Retorna True se estiver tudo pronto para iniciar.
    """
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not any([groq_key, nvidia_key, openrouter_key]):
        print("\n[CONFIG ERROR] Nenhuma chave de API de LLM (Groq, NVIDIA, OpenRouter) encontrada!")
        return False
        
    return True
