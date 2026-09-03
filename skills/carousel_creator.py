import os
import sys
import json
import re
import subprocess
import webbrowser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

KEYWORDS = [
    "criar carrossel", "gerar carrossel", "carrossel para instagram",
    "post carrossel", "fazer um carrossel", "carrossel sobre"
]

def _sanitize_filename(text):
    text = re.sub(r'laura|crie|gerar|criar|fazer|um|uma|carrossel|post|para|instagram|sobre', '', text.lower())
    text = re.sub(r'[^a-z0-9\s]', '', text.strip())
    text = re.sub(r'\s+', '_', text).strip('_')
    return text[:40] if text else "carrossel_projeto"

def _extract_json(text):
    """Extrai JSON da resposta da IA."""
    cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned.strip())
    try:
        return json.loads(cleaned)
    except:
        match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
    return None

def _generate_carousel_copy(client, model, topic):
    """Gera o texto (copy) dos 6 slides do carrossel."""
    prompt = f"""Você é um Copywriter Especialista em Carrosséis Virais de Instagram.
Crie o roteiro de um carrossel de 6 slides sobre '{topic}'.
O design será vertical (1080x1350) estilo Dark Premium.

Estrutura OBRIGATÓRIA:
Slide 1: Capa (Título ultra chamativo, fonte grande)
Slide 2: Problema / Contexto (Apresentação da dor)
Slide 3: Ponto chave 1 (Com título curto e parágrafo direto)
Slide 4: Ponto chave 2 (Outro insight poderoso)
Slide 5: O Segredo / Solução (A cereja do bolo)
Slide 6: CTA (Chamada para ação clara: curtir, salvar, comentar)

Retorne APENAS um JSON estrito neste formato:
{{
  "tema": "Tema formatado",
  "slides": [
    {{
      "numero": 1,
      "tipo": "capa",
      "titulo": "TÍTULO DA CAPA",
      "texto": "Subtítulo de apoio",
      "keyword_imagem": "termo para buscar foto de fundo"
    }},
    {{
      "numero": 2,
      "tipo": "conteudo",
      "titulo": "Título Menor",
      "texto": "Texto do slide...",
      "keyword_imagem": "termo em inglês para buscar foto"
    }}
    // ... até o 6
  ]
}}
NÃO adicione introduções ou formatações markdown. Apenas o JSON."""

    print(f"[CarouselCreator] Gerando copy para '{topic}'...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return _extract_json(response.choices[0].message.content)
    except Exception as e:
        print(f"[CarouselCreator] Erro na geração do copy: {e}")
        return None

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    if not client or not model:
        say("Meus motores de inteligência estão desligados no momento.")
        return True

    topic = re.sub(r'laura|criar|gerar|fazer|um|uma|carrossel|post|instagram|sobre', '', query.lower()).strip()
    if not topic:
        say("Qual será o tema do carrossel?")
        topic = takeCommand()
        if not topic or topic == "none":
            return True

    say(f"Entendido! Vou criar um carrossel viral sobre '{topic}'. Estruturando a copy e buscando imagens premium...")

    copy_data = _generate_carousel_copy(client, model, topic)
    if not copy_data or "slides" not in copy_data:
        say("Tive um problema ao gerar a estrutura do carrossel. Podemos tentar novamente?")
        return True

    # --- PASSO DE QA (CONTROLE DE QUALIDADE) ---
    try:
        from core.quality_controller import review_json_content
        copy_data = review_json_content(client, model, copy_data, content_type="carrossel de instagram")
    except Exception as e:
        print(f"[CarouselCreator] Erro ao instanciar Quality Controller: {e}")
    # -------------------------------------------

    # Criação das pastas
    project_slug = _sanitize_filename(topic)
    project_dir = os.path.join(BASE_DIR, "conteudos_criados", "carrosseis", project_slug)
    os.makedirs(project_dir, exist_ok=True)

    # Importa Visual Assets para pegar fotos de fundo reais
    try:
        from skills.visual_assets import get_best_photo
        visuals_enabled = True
    except ImportError:
        visuals_enabled = False
        print("[CarouselCreator] Módulo visual_assets não encontrado. Usando fundos de cor sólida.")

    html_slides = ""
    
    # Montagem do HTML
    for slide in copy_data["slides"]:
        bg_image_css = ""
        
        # Busca imagem se for capa ou CTA (para dar impacto), ou usa degradê
        if visuals_enabled and slide.get("tipo") in ["capa", "cta"]:
            kw = slide.get("keyword_imagem", topic)
            photo = get_best_photo(kw, orientation="portrait")
            if photo:
                # Efeito overlay escuro sobre a imagem
                bg_image_css = f"background: linear-gradient(to bottom, rgba(10,22,38,0.7), rgba(10,22,38,0.95)), url('{photo['url_large']}'); background-size: cover; background-position: center;"

        if not bg_image_css:
            bg_image_css = "background: linear-gradient(135deg, #0a1626, #050b14);"

        html_slides += f"""
        <div class="slide slide-{slide['tipo']}" style="{bg_image_css}">
            <div class="content">
                <div class="eyebrow">Slide {slide['numero']}/6</div>
                <h1>{slide.get('titulo', '')}</h1>
                <p>{slide.get('texto', '')}</p>
                <div class="branding">MG Solution</div>
            </div>
        </div>
        """

    # Template HTML base
    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Carrossel: {copy_data.get('tema', topic)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0; padding: 20px; background: #222;
            display: flex; flex-wrap: wrap; gap: 40px; justify-content: center;
            font-family: 'Inter', sans-serif;
        }}
        .slide {{
            width: 1080px; height: 1350px; /* Formato Instagram Retrato */
            position: relative; overflow: hidden;
            border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            display: flex; align-items: center; justify-content: center;
            color: #fff; text-align: left;
            flex-shrink: 0;
            /* transform: scale(0.5); transform-origin: top left; margin-bottom: -675px; margin-right: -540px; */
        }}
        .content {{
            width: 80%; max-width: 860px;
            z-index: 10;
        }}
        .slide-capa h1 {{
            font-size: 110px; line-height: 1.1; font-family: 'Playfair Display', serif;
            margin-bottom: 30px; color: #FFC300;
        }}
        .slide-conteudo h1 {{
            font-size: 80px; margin-bottom: 40px; color: #2EC4B6;
        }}
        .slide p {{
            font-size: 44px; line-height: 1.5; color: #E0E6ED;
        }}
        .eyebrow {{
            font-size: 30px; color: #748CAB; text-transform: uppercase; letter-spacing: 4px;
            margin-bottom: 30px; font-weight: 600;
        }}
        .branding {{
            position: absolute; bottom: 60px; right: 80px;
            font-size: 28px; font-weight: bold; color: rgba(255,255,255,0.3);
        }}
        .slide-cta h1 {{ color: #FFC300; font-size: 100px; text-align: center; }}
        .slide-cta p {{ text-align: center; font-size: 50px; }}
        .slide-cta .content {{ text-align: center; }}
    </style>
</head>
<body>
    {html_slides}
</body>
</html>"""

    html_path = os.path.join(project_dir, "carrossel.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    say(f"A estrutura do carrossel está pronta!")
    
    # Tentativa de renderização via puppeteer (script node)
    node_script_path = os.path.join(project_dir, "render.js")
    node_script = """const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 1 });
        const htmlPath = 'file://' + path.resolve(__dirname, 'carrossel.html');
        await page.goto(htmlPath, { waitUntil: 'networkidle0' });
        
        const slides = await page.$$('.slide');
        for (let i = 0; i < slides.length; i++) {
            await slides[i].screenshot({ path: path.join(__dirname, `slide_${i + 1}.png`) });
        }
        await browser.close();
        console.log("Renderização concluída.");
    } catch(e) {
        console.error("Erro na renderização:", e);
        process.exit(1);
    }
})();
"""
    with open(node_script_path, "w", encoding="utf-8") as f:
        f.write(node_script)

    say("Iniciando a renderização das imagens em alta resolução...")
    print("[CarouselCreator] Tentando rodar Puppeteer para gerar as imagens...")
    
    try:
        # Tenta rodar npx puppeteer para evitar instalação manual
        res = subprocess.run("npx -y puppeteer node render.js", cwd=project_dir, shell=True, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            say("Imagens renderizadas com sucesso!")
        else:
            print(f"[CarouselCreator] Falha no Puppeteer: {res.stderr}")
            say("Não foi possível renderizar as imagens automaticamente. Mas o arquivo de design está pronto para ser salvo.")
    except Exception as e:
        print(f"[CarouselCreator] Exceção Puppeteer: {e}")
        say("Aviso: O gerador de imagens falhou, mas a base HTML está preservada.")

    say("Abrindo a pasta com os resultados do seu carrossel.")
    webbrowser.open(f"file:///{os.path.abspath(project_dir).replace(os.sep, '/')}")
    return True
