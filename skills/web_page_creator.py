import os
import webbrowser
import json
import random
import re

KEYWORDS = [
    "link na bio", "linktree", "linkinbio", "bio", "landing page", 
    "página de vendas", "funil de vendas", "criar site", "criar página"
]

DESIGN_STYLES = {
    "glassmorphism": "Ideal para tecnologia e luxo. Usa transparências e desfoque.",
    "skeuomorphism": "Visual 3D realista. Ótimo para produtos físicos e apps intuitivos.",
    "neo brutalism": "Muito ousado e moderno. Cores fortes e bordas grossas. Atrai público jovem.",
    "claymorphism": "Fofo e amigável. Parece feito de argila. Bom para infoprodutos e crianças.",
    "minimalism": "Elegante e direto. Foco total no conteúdo. Transmite autoridade e limpeza.",
    "liquid glass": "O ápice do luxo moderno. Gradientes fluidos e animações sutis."
}

def _sanitize_filename(text):
    text = re.sub(r'laura|crie|uma|página|de|sobre|para|um|uma|landing|page|link|na|bio|estilo', '', text.lower())
    text = re.sub(r'[^a-z0-9]', '_', text.strip())
    text = re.sub(r'_+', '_', text).strip('_')
    return text[:30] if text else "projeto"

# --- CORREÇÃO AUTOMÁTICA DE TAILWIND ---
# Garante que qualquer HTML gerado pela IA use SEMPRE o Tailwind Play CDN correto
_TAILWIND_FIX = """    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        inter: ['Inter', 'sans-serif'],
                        playfair: ['Playfair Display', 'serif'],
                    },
                    backdropBlur: { xs: '2px' },
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700;900&display=swap');
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
    </style>"""

_BROKEN_TAILWIND_PATTERNS = [
    r'<link[^>]+tailwindcss[^>]+\.min\.css[^>]*>',
    r'<link[^>]+tailwind[^>]+\.css[^>]*>',
    r'<script[^>]+cdn\.tailwindcss\.com[^>]*>\s*</script>',
    r'<script[^>]+tailwindcss[^>]*>\s*</script>',
]

def _fix_html(html: str) -> str:
    """Remove qualquer versão quebrada do Tailwind e injeta o Play CDN correto."""
    # Remove todos os padrões problemáticos
    for pattern in _BROKEN_TAILWIND_PATTERNS:
        html = re.sub(pattern, '', html, flags=re.IGNORECASE)

    # Remove blocos <script> de configuração tailwind antigos se existirem
    html = re.sub(r'<script>\s*tailwind\.config\s*=\s*\{.*?\}\s*</script>', '', html, flags=re.DOTALL)

    # Injeta o bloco correto logo após o <head>
    html = re.sub(r'(<head[^>]*>)', r'\1\n' + _TAILWIND_FIX, html, count=1, flags=re.IGNORECASE)

    return html


def _get_ai_image_url(keyword, width=1200, height=800):
    clean_keyword = keyword.replace(" ", "%20").replace("\"", "")
    return f"https://image.pollinations.ai/prompt/{clean_keyword}?width={width}&height={height}&nologo=true"

def _load_business_context():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ctx = {"business_name": "", "product_name": "", "logo_url": "https://i.postimg.cc/9R26NY5h/Logo6.png"}
    try:
        path = os.path.join(BASE_DIR, "profile.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                p = json.load(f)
                ctx["business_name"] = p.get("business_name", "")
                ctx["product_name"] = p.get("main_product", {}).get("name", "")
    except: pass
    return ctx

def _build_page(client, model, ctx, briefing_data):
    """Gera o HTML final baseado em todo o briefing colhido com estética de boutique e estrutura rígida."""
    page_type = briefing_data['type']
    tema = briefing_data['topic']
    estilo = briefing_data['style']
    publico = briefing_data['audience']
    
    # Gera múltiplas variações de imagem para a vitrine
    hero_img = _get_ai_image_url(f"ultra luxury cinematic {tema} photo, dramatic lighting, 8k", 1920, 1080)
    prod_img1 = _get_ai_image_url(f"premium {tema} product shot, studio lighting, professional", 800, 800)
    prod_img2 = _get_ai_image_url(f"luxury {tema} detail macro shot, cinematic", 800, 800)
    prod_img3 = _get_ai_image_url(f"exclusive {tema} model wearing product, lifestyle luxury", 800, 800)
    
    prompt = f"""Você é uma Master Web Designer de Agência de Luxo.
Crie o código HTML completo para uma {page_type} de ALTÍSSIMO IMPACTO sobre '{tema}'.

ESTRUTURA OBRIGATÓRIA (Siga à risca):
1. <nav id="home">: Menu fixo com links funcionais para #home, #colecao, #sobre e #contato.
2. <section id="hero">: Hero Section com fundo full-screen usando a imagem {hero_img}. Deve ter um botão 'Explorar Coleção' que leva para #colecao.
3. <section id="colecao">: Grade de Produtos (GRID com 3 colunas).
   - Card 1: Imagem {prod_img1}, Título, Preço e Botão 'Comprar'.
   - Card 2: Imagem {prod_img2}, Título, Preço e Botão 'Comprar'.
   - Card 3: Imagem {prod_img3}, Título, Preço e Botão 'Comprar'.
4. <section id="sobre">: Texto persuasivo sobre a marca e autoridade.
5. <footer id="contato">: Rodapé com Botão de WhatsApp REAL: https://wa.me/5551999999999?text=Quero%20mais%20detalhes

ROTEIRO DE DESIGN (Siga à risca):
- Use o script do TAILWIND PLAY CDN: <script src="https://cdn.tailwindcss.com"></script>
- Adicione configuração de fontes no <script> do Tailwind (Inter e Playfair Display).
- Estética: '{estilo}' misturado com 'Dark Luxury' (fundo quase preto #050505, detalhes em ouro #D4AF37 ou laranja vibrante).
- Use Glassmorphism (fundos com backdrop-blur-md e bg-white/10).
- Animações: Use classes de hover, scale e transições suaves.

Retorne APENAS o código HTML completo começando com <!DOCTYPE html>. Sem conversas."""

    print(f"[LandingPage] Gerando Estrutura de Boutique ({estilo})...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "Master Designer. Retorno exclusivo: HTML completo."}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    if not client or not model: return True

    ctx = _load_business_context()
    
    # 1. INÍCIO DA CONSULTORIA HUMANIZADA
    say("Com certeza! Adoro criar novos projetos. Para fazermos algo de elite, preciso entender a alma desse site.")
    
    # Passo 1: O Tema
    tema = ""
    if len(query.split()) < 4:
        say("Sobre o que é esse projeto? Qual o produto ou serviço?")
        tema = takeCommand()
    else:
        tema = re.sub(r'laura|crie|uma|página|de|sobre|para|um|uma|landing|page|link|na|bio', '', query.lower()).strip()

    if not tema or tema == "none":
        say("Não consegui entender o tema. Vamos tentar de novo?")
        return True

    # Passo 2: O Público e Tom
    say(f"Entendido, um projeto sobre '{tema}'. E para quem a gente está falando? Público jovem, corporativo ou luxo?")
    publico = takeCommand()

    # Passo 3: O Estilo Visual
    estilos_list = list(DESIGN_STYLES.keys())
    estilos_str = ", ".join([f"{k.capitalize()}" for k in estilos_list])
    say(f"E o estilo visual? Temos {estilos_str}, ou posso escolher o melhor para você.")
    escolha_estilo = takeCommand().lower()
    
    estilo_final = random.choice(estilos_list)
    for k in estilos_list:
        if k in escolha_estilo:
            estilo_final = k
            break
    
    if any(w in escolha_estilo for w in ["sugira", "você escolhe", "melhor", "indique"]):
        # Randomiza entre os melhores estilos para não repetir sempre o mesmo
        sugestoes = ["liquid glass", "glassmorphism", "minimalism", "neo brutalism"]
        estilo_final = random.choice(sugestoes)
        say(f"Ótimo! Vou usar o estilo {estilo_final}, que combina perfeitamente com sua proposta.")
    
    say(f"Excelente. Vou orquestrar a estrutura de boutique agora. Só um momento...")

    # 2. GERAÇÃO DO PROJETO
    briefing = {
        "type": "landing page" if any(w in query.lower() for w in ["landing", "vendas", "venda"]) else "link na bio",
        "topic": tema,
        "style": estilo_final,
        "audience": publico
    }

    raw_response = _build_page(client, model, ctx, briefing)
    
    # Extração Robusta do HTML
    html_match = re.search(r'<!DOCTYPE html>.*</html>', raw_response, re.DOTALL | re.IGNORECASE)
    if html_match:
        html_code = html_match.group()
    else:
        html_code = raw_response.replace("```html", "").replace("```", "").strip()

    # 3. SALVAMENTO E FINALIZAÇÃO
    nome_projeto = _sanitize_filename(tema)
    sites_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sites_criados")
    os.makedirs(sites_dir, exist_ok=True)
    filename = f"site_{nome_projeto}.html"
    filepath = os.path.join(sites_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_code)
    
    say(f"Pronto! O seu site estilo {estilo_final} foi concluído e está no ar. O que achou desse novo design?")
    webbrowser.open(f"file://{filepath}")
    return True