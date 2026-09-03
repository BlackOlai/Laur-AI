import os
import base64
from openai import OpenAI

KEYWORDS = [
    "analisar imagem", "o que tem nesta foto", "descrever imagem",
    "analisar print", "ler imagem", "visão computacional", "ver imagem",
    "analisar foto", "[IMAGEM ANEXADA:"
]

def encode_image(image_path):
    """Converte a imagem em base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    # Extrair caminho da imagem se vier do comando do widget
    image_path = None
    if "[IMAGEM ANEXADA:" in query:
        try:
            image_path = query.split("[IMAGEM ANEXADA:")[1].split("]")[0].strip()
        except:
            pass

    if not image_path:
        say("Por favor, anexe uma imagem no widget para que eu possa analisar.")
        return True

    if not os.path.exists(image_path):
        say("Desculpe senhor, não consegui localizar o arquivo da imagem.")
        return True

    say("Processando imagem e ativando sensores visuais...")

    # Tentar usar um modelo de visão específico se estiver no Groq
    vision_model = "llama-3.2-11b-vision-preview" 
    # Se estiver usando OpenRouter, podemos usar outro
    if "openrouter" in str(client.base_url).lower():
        vision_model = "google/gemini-flash-1.5" # Exemplo de modelo vision no OpenRouter

    try:
        base64_image = encode_image(image_path)
        
        # Faz a chamada usando a API de visão
        response = client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analise esta imagem detalhadamente. Se for um site, foque no design e UX. Se for um anúncio, foque nos gatilhos e marketing. Se for um erro, me ajude a diagnosticar."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000
        )
        
        analise = response.choices[0].message.content
        say("Aqui está minha análise visual, senhor:")
        say(analise)
        
    except Exception as e:
        print(f"Erro na análise visual: {e}")
        say("Ocorreu um erro ao tentar processar a visão computacional. Verifique se o modelo suporta imagens.")
    
    return True
