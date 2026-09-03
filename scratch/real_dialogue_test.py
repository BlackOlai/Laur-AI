import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# Adiciona a raiz ao path
ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)

load_dotenv()

from Laura import chat, get_ai_client
from skills.skill_router import execute as route_intent
from core.tts import say

# Mock do say para não gerar áudio no servidor (apenas logar)
def mock_say(text):
    print(f"\n[LAURA RESPONDEU]: {text}")

def test_real_ai_dialogue():
    client, model = get_ai_client()
    context = {
        "client": client,
        "model_to_use": model,
        "say": mock_say
    }
    
    print(f"=== INICIANDO TESTE DE DIÁLOGO REAL (Motor: {model}) ===")
    
    queries = [
        "Olá Laura, como estão os negócios hoje?",
        "Qual a previsão do tempo para amanhã?",
        "Me conte uma curiosidade sobre inteligência artificial."
    ]
    
    for q in queries:
        print(f"\n> USUÁRIO PERGUNTOU: {q}")
        
        # Tenta o roteador primeiro (como no loop real)
        print("... Analisando intenção ...")
        if not route_intent(q, mock_say, lambda **kwargs: "none", context):
            # Se o roteador não achar skill, vai pro chat geral
            print("... Usando Inteligência Geral ...")
            chat(q)
        
        time.sleep(1) # Pequena pausa entre interações

if __name__ == "__main__":
    test_real_ai_dialogue()
