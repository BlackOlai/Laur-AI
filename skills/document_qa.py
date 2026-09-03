import os
import tkinter as tk
from tkinter import filedialog
import time

KEYWORDS = ["ler pdf", "ler arquivo", "analise o documento", "resuma o documento", "perguntar sobre o arquivo", "ler documento", "analisar arquivo"]

def get_llm_cfg():
    """Retorna as configurações de LLM para o Qwen-Agent no formato esperado."""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    if GROQ_API_KEY:
        return {
            'model': 'llama-3.3-70b-versatile',
            'model_server': 'https://api.groq.com/openai/v1',
            'api_key': GROQ_API_KEY
        }
    elif NVIDIA_API_KEY:
        return {
            'model': 'minimaxai/minimax-m2.7',
            'model_server': 'https://integrate.api.nvidia.com/v1',
            'api_key': NVIDIA_API_KEY
        }
    else:
        return {
            'model': 'google/gemini-2.0-pro-exp-02-05:free',
            'model_server': 'https://openrouter.ai/api/v1',
            'api_key': OPENROUTER_API_KEY
        }

def select_file():
    """Abre uma janela nativa para o usuário escolher o documento."""
    root = tk.Tk()
    root.withdraw() # Oculta a janela principal do Tkinter
    root.attributes('-topmost', True) # Força a janela a abrir por cima de todas
    
    file_path = filedialog.askopenfilename(
        title="Selecione o documento para a Laura ler",
        filetypes=[
            ("Documentos suportados", "*.pdf *.docx *.txt *.md *.csv"),
            ("Todos os Arquivos", "*.*")
        ]
    )
    root.destroy()
    return file_path

def execute(query, say, takeCommand, context=None):
    say("Certo. Vou abrir uma janela para você selecionar o arquivo que deseja analisar.")
    
    file_path = select_file()
    
    if not file_path:
        say("Você cancelou a seleção. Se precisar de algo, é só chamar.")
        return True
        
    say("Documento carregado. O que você gostaria de saber ou que eu faça com ele?")
    
    pergunta, _ = takeCommand(timeout=30, return_source=True)
    if not pergunta or pergunta.lower() in ["nada", "deixa pra lá", "cancelar"]:
        say("Tudo bem, análise cancelada.")
        return True

    # Se o takeCommand voltar vazio mas houver query, usamos a query inicial se ela tiver instruções (ex: "resuma o documento x")
    if not pergunta:
        pergunta = query

    try:
        from qwen_agent.agents import Assistant
    except ImportError:
        say("Olair, a biblioteca de análise de documentos ainda está sendo instalada no sistema. Aguarde alguns instantes e tente de novo.")
        return True
    
    set_status = context.get("set_status") if context else lambda x,y: None
    set_status("thinking", "Lendo documento e buscando resposta...")
    say("Iniciando a leitura inteligente do arquivo.")

    try:
        llm_cfg = get_llm_cfg()
        bot = Assistant(llm=llm_cfg)
        
        # Padrão multi-modal do Qwen-Agent: lista com o texto da pergunta + objeto de arquivo
        messages = [{
            'role': 'user', 
            'content': [
                {'text': pergunta + "\nResponda em PT-BR."},
                {'file': file_path}
            ]
        }]

        # Qwen-Agent resolve o chunking/RAG nativamente
        say("Isso pode levar alguns segundos dependendo do tamanho do arquivo.")
        
        responses = bot.run(messages)
        
        # O generator retorna resultados parciais, o último tem a resposta final
        final_response = ""
        for resp in responses:
            if resp:
                final_response = resp[-1]['content']
                
        # Algumas vezes, the agent returns tools format if it fails, verify string
        if isinstance(final_response, list):
            final_text = "\n".join([item.get('text', '') for item in final_response if 'text' in item])
        else:
            final_text = final_response

        # Resposta final em voz/texto
        say(final_text)
        
    except Exception as e:
        print(f"[Document RAG Error]: {e}")
        say("Houve um erro técnico ao processar este arquivo. Pode ser que o formato não seja suportado ou ele seja muito grande para o modelo atual.")

    return True
