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
    "criar ebook", "gerar ebook", "fazer um ebook", "escrever ebook",
    "criar um e-book", "e-book sobre", "ebook sobre", "livro digital"
]

def _sanitize_filename(text):
    text = re.sub(r'laura|crie|gerar|criar|fazer|um|uma|ebook|e-book|livro|digital|sobre', '', text.lower())
    text = re.sub(r'[^a-z0-9\s]', '', text.strip())
    text = re.sub(r'\s+', '_', text).strip('_')
    return text[:40] if text else "ebook_projeto"

def _generate_ebook_content(client, model, topic):
    """Gera o conteúdo Markdown completo do e-book estruturado."""
    prompt = f"""Você é um Ghostwriter Expert em Infoprodutos.
Sua missão é escrever o rascunho completo de um E-book de alto valor sobre '{topic}'.

A estrutura do documento DEVE ser rigorosamente em Markdown e conter:
1. Título do E-book (H1)
2. Subtítulo magnético
3. Sobre o Autor (MG Solution)
4. Introdução impactante
5. Capítulo 1: O fundamento principal (H2 para capítulos, H3 para seções)
6. Capítulo 2: A estratégia prática
7. Capítulo 3: Erros comuns e como evitá-los
8. Conclusão e CTA (Para onde o leitor deve ir a seguir?)

Regras de Estilo:
- Direto ao ponto, linguagem persuasiva e profissional.
- Use bullet points e negritos para facilitar a leitura.
- Não precisa ser gigantesco, cerca de 800 a 1500 palavras está ótimo para este rascunho de alta conversão.
- Retorne APENAS o texto em Markdown (nada de json, apenas markdown puro).
"""

    print(f"[EbookCreator] Escrevendo e-book sobre '{topic}'...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[EbookCreator] Erro na geração do texto: {e}")
        return None

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    
    if not client or not model:
        say("Meus motores de inteligência estão desligados.")
        return True

    topic = re.sub(r'laura|criar|gerar|fazer|um|uma|ebook|e-book|livro|digital|sobre', '', query.lower()).strip()
    if not topic:
        say("Qual será o tema do E-book?")
        topic = takeCommand()
        if not topic or topic == "none":
            return True

    say(f"Perfeito. Vou iniciar a criação do E-book sobre '{topic}'. Primeiro, escrevendo o conteúdo focado em alta conversão...")

    markdown_content = _generate_ebook_content(client, model, topic)
    if not markdown_content:
        say("Tive um problema ao redigir o e-book. Podemos tentar novamente?")
        return True

    # --- PASSO DE QA (CONTROLE DE QUALIDADE) ---
    try:
        from core.quality_controller import review_markdown_content
        markdown_content = review_markdown_content(client, model, markdown_content, content_type="e-book de alta conversão")
    except Exception as e:
        print(f"[EbookCreator] Erro ao instanciar Quality Controller: {e}")
    # -------------------------------------------

    # Criação das pastas
    project_slug = _sanitize_filename(topic)
    project_dir = os.path.join(BASE_DIR, "conteudos_criados", "ebooks", project_slug)
    os.makedirs(project_dir, exist_ok=True)

    # Busca capa via Visual Assets
    capa_markdown = ""
    try:
        from skills.visual_assets import get_best_photo
        photo = get_best_photo(topic, orientation="portrait")
        if photo:
            say("Encontrei uma foto profissional fantástica para usar como capa do E-book.")
            capa_markdown = f"""
<div style="text-align:center; margin-bottom: 50px;">
  <img src="{photo['url_large']}" alt="Capa" style="width: 100%; max-height: 800px; object-fit: cover; border-radius: 10px;">
</div>
"""
    except ImportError:
        print("[EbookCreator] visual_assets não disponível para capa.")

    # Injeta CSS para a formatação do PDF
    css_injection = """
<style>
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
    h1 { color: #1a2a3a; font-size: 3em; border-bottom: 2px solid #FFC300; padding-bottom: 10px; margin-top: 50px; }
    h2 { color: #2a3a4a; margin-top: 40px; }
    h3 { color: #3a4a5a; }
    blockquote { border-left: 5px solid #FFC300; padding-left: 15px; font-style: italic; color: #555; }
    .page-break { page-break-before: always; }
</style>
"""

    final_markdown = css_injection + capa_markdown + markdown_content

    md_path = os.path.join(project_dir, "livro.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(final_markdown)

    say("O texto está pronto! Convertendo o documento para PDF profissional de alta qualidade...")

    pdf_path = os.path.join(project_dir, f"{project_slug}.pdf")

    # Tenta usar npx md-to-pdf para conversão autônoma
    print(f"[EbookCreator] Gerando PDF via md-to-pdf...")
    try:
        # A flag -y no npx instala automaticamente se não existir
        res = subprocess.run(f'npx -y md-to-pdf livro.md --stylesheet ""', cwd=project_dir, shell=True, capture_output=True, text=True, timeout=120)
        
        # O md-to-pdf gera o arquivo com o mesmo nome .pdf
        generated_pdf = os.path.join(project_dir, "livro.pdf")
        if os.path.exists(generated_pdf):
            os.rename(generated_pdf, pdf_path)
            say("E-book finalizado e renderizado em PDF com sucesso!")
        else:
            print(f"[EbookCreator] md-to-pdf não gerou o PDF. Erro: {res.stderr}")
            say("Não foi possível converter automaticamente para PDF, mas o documento Markdown original está salvo e formatado.")
    except Exception as e:
        print(f"[EbookCreator] Erro crítico md-to-pdf: {e}")
        say("Houve um erro na conversão do PDF.")

    say("Abrindo o local do seu novo Infoproduto.")
    webbrowser.open(f"file:///{os.path.abspath(project_dir).replace(os.sep, '/')}")
    return True
