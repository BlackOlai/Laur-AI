import os
import sys
import json
import requests
from io import BytesIO

# Import PIL (Pillow)
try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
except ImportError:
    print("[ThumbnailCreator] Erro: Pillow não instalado. Execute 'pip install pillow'")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from skills import visual_assets
from core import quality_controller

THUMB_DIR = os.path.join(BASE_DIR, "assets_baixados", "thumbnails")
os.makedirs(THUMB_DIR, exist_ok=True)

def load_channel_config(channel_id):
    config_path = os.path.join(BASE_DIR, "config", "quality_guidelines.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("canais", {}).get(channel_id)
    except Exception as e:
        print(f"[ThumbnailCreator] Erro ao carregar config: {e}")
        return None

def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))

def create_thumbnail(channel_id, video_title, theme_keyword):
    """
    Cria uma thumbnail viral baseada no canal.
    """
    # 1. Carregar Configurações do Canal
    config = load_channel_config(channel_id)
    if not config:
        print(f"[ThumbnailCreator] Canal {channel_id} não encontrado no JSON.")
        return None
        
    text_color = config["cores_primarias"][0] # Ex: #FFD700
    
    # 2. Gerar Gancho (Hook) para a capa
    groq_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    
    hook_text = "O SEGREDO REVELADO" # Fallback inicial
    prompt = f"Crie um título curtíssimo (gancho) de no máximo 4 palavras para uma capa de vídeo do YouTube. O título original é: '{video_title}'. O canal é de {config['nicho']}. Seja super apelativo e misterioso. Retorne APENAS as 4 palavras em MAIÚSCULAS, sem aspas."
    
    if groq_key:
        try:
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                hook_text = res.json()["choices"][0]["message"]["content"].replace('"', '').strip()
        except Exception as e:
            print(f"[ThumbnailCreator] Erro na geração do Hook (Groq): {e}")
        
    print(f"[ThumbnailCreator] Hook gerado: '{hook_text}'")

    # 3. Baixar Imagem de Fundo
    print(f"[ThumbnailCreator] Buscando fundo para '{theme_keyword}'...")
    photo = visual_assets.get_best_photo(theme_keyword, orientation="landscape")
    if not photo:
        print("[ThumbnailCreator] Não foi possível encontrar uma imagem de fundo.")
        return None
        
    try:
        response = requests.get(photo["url_large"], timeout=15)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"[ThumbnailCreator] Erro ao baixar imagem: {e}")
        return None
        
    # 4. Formatar a imagem (1280x720)
    target_w, target_h = 1280, 720
    # Redimensionar mantendo a proporção para preencher a tela
    ratio = max(target_w / img.width, target_h / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    img = crop_center(img, target_w, target_h)
    
    # Escurecer um pouco e aumentar contraste (Vignette effect simulated)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5) # Fundo dark premium
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    
    # 5. Adicionar o Texto
    # Usando a fonte Impact nativa do Windows, que é ideal para Thumbnails
    try:
        font_path = "C:\\Windows\\Fonts\\impact.ttf"
        font = ImageFont.truetype(font_path, 120)
    except IOError:
        try:
            font = ImageFont.truetype("arialbd.ttf", 100)
        except IOError:
            font = ImageFont.load_default()
            
    txt_layer = Image.new('RGBA', img.size, (255,255,255,0))
    draw = ImageDraw.Draw(txt_layer)
    
    # Posicionar texto no centro
    # textbbox is available in newer Pillow versions
    try:
        bbox = draw.textbbox((0,0), hook_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older Pillow
        text_w, text_h = draw.textsize(hook_text, font=font)
        
    x = (target_w - text_w) / 2
    y = (target_h - text_h) / 2
    
    # Borda/Stroke e Sombra preta profunda
    shadowcolor = "black"
    stroke_width = 8
    
    for adj_x in range(-stroke_width, stroke_width+1, 2):
        for adj_y in range(-stroke_width, stroke_width+1, 2):
            draw.text((x+adj_x, y+adj_y+10), hook_text, font=font, fill=shadowcolor) # Sombra e borda

    # Texto principal
    draw.text((x, y), hook_text, font=font, fill=text_color)
    
    # Combinar tudo
    final_img = Image.alpha_composite(img, txt_layer).convert("RGB")
    
    # Salvar
    filename = f"{channel_id}_{hook_text.replace(' ', '_')[:15]}.jpg"
    filepath = os.path.join(THUMB_DIR, filename)
    final_img.save(filepath, "JPEG", quality=95)
    
    print(f"[ThumbnailCreator] Thumbnail criada com sucesso: {filepath}")
    return filepath

def execute(query, say, takeCommand, context=None):
    """Interface de voz"""
    try:
        from core import calendar_manager
    except ImportError:
        calendar_manager = None
        
    say("Iniciando gerador de thumbnail. Qual o título do vídeo que você gravou?")
    title = takeCommand()
    if not title or title == "none":
        return True
        
    say("Qual a palavra chave visual para a imagem de fundo? Por exemplo: homem rico, leão, paisagem.")
    keyword = takeCommand()
    
    say("Para qual canal devo criar essa thumbnail? Diga Visão Milionária, Corpo de Titã, ou Fé Revelada.")
    canal = takeCommand()
    
    canal_id = "visao_milionaria"
    if "corpo" in canal.lower() or "titã" in canal.lower():
        canal_id = "corpo_de_tita"
    elif "fé" in canal.lower() or "revelada" in canal.lower():
        canal_id = "fe_revelada"
    
    say(f"Gerando a thumbnail premium para o canal escolhido. Aguarde um instante...")
    filepath = create_thumbnail(canal_id, title, keyword)
    
    if filepath:
        say("Thumbnail gerada com sucesso!")
        
        if calendar_manager:
            say("Você quer que eu já guarde essa thumbnail na pasta de agendamento? Diga sim ou não.")
            resp = takeCommand()
            if resp and "sim" in resp.lower():
                say("Para qual dia da semana? Diga de segunda a domingo.")
                dia = takeCommand()
                say("Qual turno? Diga manhã, tarde ou noite.")
                turno = takeCommand()
                
                final_path = calendar_manager.allocate_file(filepath, canal_id, dia, turno)
                if final_path:
                    say("Feito! Thumbnail alocada na gaveta correta do calendário.")
                else:
                    say("Não entendi o dia ou turno, deixei a thumbnail na pasta geral de assets.")
    else:
        say("Houve um erro ao gerar a thumbnail.")
        
    return True
