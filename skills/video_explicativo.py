# -*- coding: utf-8 -*-
import os
import subprocess
import json
import re
import wave
import contextlib
import shutil
import webbrowser

# Importa os códigos estáticos dos assets
try:
    from video_explicativo_assets import FETCH_FONTS_CODE, COMPOSITION_TEMPLATE_CODE
except ImportError:
    from skills.video_explicativo_assets import FETCH_FONTS_CODE, COMPOSITION_TEMPLATE_CODE

# Importa utilitários de assets de mídia (fotos, vídeos, áudio)
try:
    from visual_assets import get_best_photo, get_best_video
    from audio_assets import get_best_audio
    _assets_available = True
except ImportError:
    try:
        from skills.visual_assets import get_best_photo, get_best_video
        from skills.audio_assets import get_best_audio
        _assets_available = True
    except ImportError:
        _assets_available = False
        print("[VideoExplicativo] Aviso: skills de assets (visual/audio) não disponíveis.")

KEYWORDS = [
    "criar vídeo", "criar video", "crie um vídeo", "crie um video", "cria vídeo", "cria video", "cria um vídeo", "cria um video", "gerar vídeo explicativo", "gerar video explicativo",
    "fazer um vídeo", "fazer um video", "fazer vídeo", "fazer video", "faz vídeo", "faz video", "faz um vídeo", "faz um video", "gera vídeo", "gera video", "gera um vídeo", "gera um video", "gerar vídeo", "gerar video",
    "vídeo sobre", "video sobre", "vídeo de", "video de", "vídeo para", "video para", "vídeo explicativo", "video explicativo", "vídeo do inema", "video do inema",
    "vídeo para shorts", "video para shorts", "produzir vídeo", "produzir video", "mini tutorial em vídeo", "mini tutorial em video",
    "montar vídeo", "montar video", "monta vídeo", "monta video", "produz vídeo", "produz video", "vídeo agora", "video agora", "faz vídeo agora", "fazer vídeo agora"
]

def _sanitize_filename(text):
    text = re.sub(r'laura|criar|crie|cria|gerar|gera|vídeo|vídeos|explicativo|sobre|fazer|faz|um|uma|inema', '', text.lower())
    text = re.sub(r'[^a-z0-9\s]', '', text.strip())
    text = re.sub(r'\s+', '_', text).strip('_')
    return text[:40] if text else "video_projeto"

def load_channel_config(channel_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "quality_guidelines.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("canais", {}).get(channel_id)
    except Exception as e:
        print(f"[VideoExplicativo] Erro ao carregar config: {e}")
        return None

def hex_to_rgb_str(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return f"{int(hex_color[0:2], 16)},{int(hex_color[2:4], 16)},{int(hex_color[4:6], 16)}"
    return "255,195,0" # Fallback amber

def get_audio_duration(file_path):
    """Mede a duração exata do áudio usando wave (WAV) ou ffprobe (qualquer formato)."""
    # Tenta WAV nativo primeiro
    if file_path.endswith('.wav') and os.path.exists(file_path):
        try:
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                nchannels = f.getnchannels()
                sampwidth = f.getsampwidth()
                
                # Cobre cabeçalhos malformados/incompletos

                real_size = os.path.getsize(file_path)
                bytes_per_frame = sampwidth * nchannels
                if bytes_per_frame > 0:
                    max_possible = (real_size - 44) // bytes_per_frame
                    if frames > max_possible:
                        frames = max_possible
                
                dur = round(frames / float(rate), 3)
                if dur < 300:  # Sanity check
                    return dur
        except Exception:
            pass

    # Fallback: ffprobe (funciona com WAV, MP3, etc.)
    if os.path.exists(file_path):
        try:
            result = subprocess.run(
                f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{file_path}"',
                shell=True, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return round(float(result.stdout.strip()), 3)
        except Exception as e:
            print(f"[VideoExplicativo] ffprobe falhou para {file_path}: {e}")

    print(f"[VideoExplicativo] Arquivo de áudio não encontrado ou ilegível: {file_path}. Usando 5s como fallback.")
    return 5.0  # Fallback padrão

def _sanitize_for_json(text):
    """Converte template literals JS (backticks) para strings JSON seguras."""
    import re
    # Substitui blocos de backtick: `...` -> "..."
    # Isso captura backticks que o LLM usa como delimitadores de string JS
    def replace_backtick(m):
        inner = m.group(1)
        # Escapa aspas duplas dentro do conteúdo capturado
        inner = inner.replace('\\"', '\\\\"')  # preserve already-escaped quotes
        inner = inner.replace('"', '\\"')
        # Remove newlines que quebrariam o JSON
        inner = inner.replace('\n', ' ').replace('\r', '')
        return '"' + inner + '"'
    return re.sub(r'`(.*?)`', replace_backtick, text, flags=re.DOTALL)


def _strip_markdown_fences(text):
    """Remove marcações de bloco de código markdown, incluindo variações."""
    import re
    # Remove ```json ... ``` ou ``` ... ```
    cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned.strip())
    return cleaned.strip()


def _extract_json(text):
    """Extrai e parseia um JSON de uma resposta de texto de forma robusta."""
    import re

    # Etapa 1: Remove markdown fences
    cleaned = _strip_markdown_fences(text)

    # Etapa 2: Tenta parse direto
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Etapa 3: Sanitiza backtick template literals e tenta novamente
    sanitized = _sanitize_for_json(cleaned)
    try:
        return json.loads(sanitized)
    except Exception as e:
        print(f"[VideoExplicativo] Erro ao fazer parse de JSON após sanitização de backticks: {e}")

    # Etapa 4: Extrai o primeiro bloco { ... } com regex e tenta as duas versões
    match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
    if match:
        block = match.group(1)
        try:
            return json.loads(block)
        except Exception:
            pass
        sanitized_block = _sanitize_for_json(block)
        try:
            return json.loads(sanitized_block)
        except Exception as e:
            print(f"[VideoExplicativo] Erro ao fazer parse de JSON extraído por regex: {e}")

    print(f"[VideoExplicativo] Erro de parse JSON geral: todos os métodos falharam.")
    return None

def _fetch_bible_verses_for_topic(topic, canal_id):
    """
    Busca de 2 a 4 versículos bíblicos REAIS e relevantes ao tema do vídeo.
    Retorna uma string com os textos completos para enriquecer o prompt de roteiro.
    """
    try:
        from skills.bible_reference import get_bible_verse
    except ImportError:
        try:
            from bible_reference import get_bible_verse
        except ImportError:
            return ""

    # Mapeamento de temas para versículos relevantes
    verse_pool = {
        # Temas de fé / espírito / mistérios bíblicos
        "fe": [
            "Hebrews 11:1", "Romans 8:28", "Matthew 17:20", "Psalms 46:1",
            "Jeremiah 29:11", "Isaiah 41:10", "John 3:16"
        ],
        "espirito": [
            "John 14:26", "Acts 1:8", "Romans 8:11", "1 Corinthians 2:10",
            "Galatians 5:22", "Ezekiel 36:27"
        ],
        "poder": [
            "Philippians 4:13", "2 Timothy 1:7", "Isaiah 40:31", "Psalms 18:32",
            "Romans 8:37", "1 John 4:4"
        ],
        "amor": [
            "1 Corinthians 13:4", "John 15:13", "Romans 5:8", "1 John 4:8",
            "Song of Solomon 8:6"
        ],
        "milagre": [
            "Matthew 19:26", "Luke 1:37", "Mark 9:23", "John 11:40",
            "Numbers 23:19"
        ],
        "profecias": [
            "Isaiah 7:14", "Micah 5:2", "Daniel 9:25", "Psalms 22:16",
            "Isaiah 53:5", "Zechariah 9:9"
        ],
        "default": [
            "Psalms 23:1", "Jeremiah 29:11", "Romans 8:28", "Isaiah 40:31",
            "Philippians 4:13", "John 3:16", "Hebrews 11:1"
        ]
    }

    # Detecta tema pelo assunto
    topic_lower = topic.lower()
    selected_pool = verse_pool["default"]
    for key in verse_pool:
        if key != "default" and key in topic_lower:
            selected_pool = verse_pool[key]
            break

    import random
    chosen_refs = random.sample(selected_pool, min(3, len(selected_pool)))

    verses_text = []
    for ref in chosen_refs:
        vd = get_bible_verse(ref)
        if vd and vd.get("text"):
            verses_text.append(f'"{vd["text"].strip()}" ({vd["reference"]})')

    return "\n".join(verses_text) if verses_text else ""


def _build_script(client, model, topic, config, render_vertical=True):
    """Solicita à IA que escreva o roteiro do vídeo explicativo em formato JSON."""

    # Busca versículos bíblicos reais ANTES de gerar o roteiro
    canal_id = config.get("_canal_id", "")
    bible_verses_text = ""
    if config.get("nicho", "") and any(
        w in config["nicho"].lower() for w in ["bíbl", "bibl", "fé", "fe", "espi", "religi"]
    ):
        print("[VideoExplicativo] Buscando versículos bíblicos reais para enriquecer o roteiro...")
        bible_verses_text = _fetch_bible_verses_for_topic(topic, canal_id)
        if bible_verses_text:
            print(f"[VideoExplicativo] Versículos encontrados:\n{bible_verses_text}")

    # Também usa o contexto_extra se existir
    contexto_base = config.get('contexto_extra', '')
    if bible_verses_text:
        contexto_final = bible_verses_text
        if contexto_base and contexto_base not in bible_verses_text:
            contexto_final = bible_verses_text + "\n" + contexto_base
    else:
        contexto_final = contexto_base or 'Aja com sabedoria e crie com propósito.'

    # Estrutura de cenas adaptada ao nicho
    nicho = config.get("nicho", "").lower()
    if any(w in nicho for w in ["bíbl", "bibl", "fé", "religi", "espi"]):
        estrutura_cenas = """    1. GANCHO BOMBSTICO: Uma pergunta ou revelação chocante que ninguém espera. Comece com impacto puro.
    2. A VERDADE OCULTA: O que a maioria das pessoas não sabe sobre o assunto. Gere intriga.
    3. A PROVA DAS ESCRITURAS: Cita o texto LITERAL de um versículo fornecido (palavra por palavra). Não resuma.
    4. O MISTRIO REVELADO: Explica a profundidade do significado. Use linguagem epica e cinematica.
    5. A TRANSFORMÃO: Como esse ensinamento muda a vida de quem acredita. Emocional e pessoal.
    6. O CONFRONTO: O que acontece com quem ignora essa verdade. Crie urgencia.
    7. O TESTEMUNHO: Um exemplo real ou anedota poderosa sobre o tema.
    8. O CHAMADO: Fecha com uma declaração de fé inspiradora. As últimas palavras devem arrepiar."""
    else:
        estrutura_cenas = """    1. Hook (gancho inicial com pergunta ou fato impactante)
    2. Primeiro princípio (essência simples do assunto)
    3. Anatomia/Mecânica (como se estrutura/funciona)
    4. Conceito-chave (divulgação progressiva ou core concept)
    5. Onde vive / Como instalar / Aplicação (prática)
    6. Nível avançado (fluxos, referências, templates)
    7. Exemplo real do mundo prático (um caso prático de uso)
    8. Conclusão / Fecho (resumo rápido para fechar com chave de ouro)"""

    import random
    variation_seed = random.randint(1000, 9999)

    prompt = f"""Você é o roteirista mais emocionante e impactante de conteúdo religioso do Brasil. 
    Seu vídeo sobre '{topic}' deve causar ARREPIOS, EMOÇÃO e TRANSFORMAÇÃO. É para o canal {config['nome']} (Nicho: {config['nicho']}).
    
    [SEMENTE DE VARIAÇÃO CRIATIVA: #{variation_seed} - GERE UMA ABORDAGEM NOVA E ÚNICA!]

    VERSÍCULOS BÍBLICOS REAIS PARA USAR (textos LITERAIS — copie e use exatamente como estão):
    {contexto_final}
    
    ESTRUTURA OBRIGATÓRIA DAS 8 CENAS (NÃO inclua a cena 9 — ela é o CTA pré-definido):
{estrutura_cenas}
    
    REGRAS CRÍTICAS DE COPY:
    - Idioma: Português (PT-BR), linguagem poderosa, direta, emocionante.
    {'- FORMATO VERTICAL (Shorts/TikTok): O vídeo inteiro deve durar entre 30 e 60 segundos. CADA cena deve ter NO MÁXIMO 1 frase curta com até 15 palavras. PROIBIDO escrever mais que isso. Seja ULTRA direto e impactante.' if render_vertical else '- FORMATO HORIZONTAL (Vídeo longo): O vídeo deve durar entre 3 e 5 minutos. Cada cena pode ter de 2 a 4 frases detalhadas. Aprofunde o tema com clareza.'}
    - PROIBIDO dizer apenas "João 3:16" ou "Salmos 23". Use o TEXTO LITERAL do versículo na narração.
    - PROIBIDO frases genéricas como "Neste vídeo vamos explorar..." ou "Bem-vindos ao canal".
    - OBRIGATÓRIO: A cena 1 deve prender em menos de 3 segundos. Comece no meio da ação.
    - OBRIGATÓRIO: Pelo menos UMA cena deve citar o texto LITERAL de um dos versículos acima, completo.
    - Cadência humana: não seja robótico. Varie o ritmo.
    - Estética: {config['vibe']}
    - Legenda (caption): Máximo 60 caracteres por cena. Deve ser impactante, não descritiva.
    - visual_desc: Descreva um cenário visual cinematográfico para a cena (para busca de imagens).
    
    Retorne o roteiro APENAS no formato JSON estrito:
    {{
      "titulo": "Título Impactante do Vídeo",
      "cenas": [
        {{
          "numero": 1,
          "titulo_cena": "GANCHO BOMBA",
          "texto_original": "E se a Bíblia guardasse um segredo que mudaria tudo o que você acredita?",
          "texto_fala": "E se a Bíblia guardasse um segredo que mudaria tudo o que você acredita?",
          "caption": "O segredo que a Bíblia esconde",
          "visual_desc": "Bíblia antiga aberta com luz divina dourada irradiando das páginas"
        }},
        ... (Gere exatamente 8 cenas)
      ]
    }}
    Responda APENAS o JSON. Sem explicações, introduções ou notas."""

    print(f"[VideoExplicativo] Gerando roteiro emocional para '{topic}'...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Você é o melhor roteirista de conteúdo religioso emocional do Brasil. Escreve em PT-BR com linguagem poderosa que toca o coração. Retorno exclusivo em JSON válido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9  # Mais criatividade para copy emocional
    )
    return _extract_json(response.choices[0].message.content)

def _generate_composition_code(client, model, script_data, config, max_retries=2):
    """Solicita à IA a geração do código HTML e animações GSAP específicos para as 8 cenas.
    Tenta até max_retries vezes em caso de falha de parse JSON.
    """
    prompt = f"""Você é a Desenvolvedora Frontend e Especialista em Motion Design de elite da Laura.
    Com base no roteiro a seguir, crie as cenas HTML e animações GSAP correspondentes.
    
    Roteiro:
    {json.dumps(script_data, indent=2, ensure_ascii=False)}
    
    Sua tarefa é gerar o código que será inserido no template build-index.mjs.
    Retorne APENAS um objeto JSON estrito com dois campos:
    
    1. "scenes": dicionário de "scene1" a "scene8" cujo VALOR é uma string HTML pura.
       REGRA CRÍTICA: use aspas simples (') para atributos HTML dentro da string. Isso evita erros de JSON parse!
       NUNCA use backticks (`).
       Exemplo correto:
       {{
         "scene1": "<div class='eyebrow'><span class='dot'></span>HOOK</div><h1 class='title'>Título <span class='accent'>Destaque</span></h1>",
         "scene2": "<div class='eyebrow'>PRINCÍPIO</div><h1 class='title'>Conteúdo</h1>"
       }}
       
    2. "animations": dicionário de "1" a "8" cujo VALOR é código GSAP sem declaração de case/break.
       Use at(delta) para timing. IDs de elementos: #s1-title, #s1-sub, etc.
       NUNCA use backticks. Strings JS dentro do JSON devem usar aspas simples (').
       Exemplo correto:
       {{
         "1": "tl.from('#s1-title', {{y: 50, opacity: 0, duration: 0.6, ease: 'power3.out'}}, at(0.2));",
         "2": "tl.from('#s2-title', {{y: 40, opacity: 0, duration: 0.5}}, at(0.1));"
        }}
       
    REGRAS DE ESTILO E DESIGN:
    - O canal é {config['nome']} focado em {config['nicho']}.
    - Vibe: {config['vibe']}.
    - Classes CSS disponíveis: accent (cor principal), accent2 (cor secundária), dim, mono, code, kicker, h2, lead.
    - Layout de duas colunas: use classe grid2 com divs left e right.
    - IDs únicos por cena: prefixe com s(numero) ex: id=\\"s1-title\\".
    - Animações GSAP: use tl.from, tl.to, tl.fromTo com transforms y/x, scale, opacity fluídos.

    REGRA ABSOLUTA — PROIBIDO:
    - NUNCA use a tag <img> com src local (ex: <img src='foto.png'>). Não existem imagens locais.
    - A visualização deve ser EXCLUSIVAMENTE com HTML estrutural (divs, spans) e classes CSS.
    - Para representar imagens, use divs ou emojis estilizados.
    
    IMPORTANTE: Responda APENAS o JSON. Sem explicações, sem blocos de código markdown, sem comentários."""

    for attempt in range(1, max_retries + 1):
        print(f"[VideoExplicativo] Gerando composições visuais e animações GSAP via LLM (tentativa {attempt}/{max_retries})...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um Frontend Developer especialista em GSAP e HTML. Retorne APENAS JSON válido. NUNCA use backticks como delimitadores de string. Use apenas aspas simples dentro do HTML."},
                {"role": "user", "content": prompt}
            ]
        )
        raw = response.choices[0].message.content
        result = _extract_json(raw)
        if result and "scenes" in result and "animations" in result:
            return result
        print(f"[VideoExplicativo] Tentativa {attempt} falhou. Resposta bruta:\n{raw[:1000]}")

    print("[VideoExplicativo] Todas as tentativas de geração de composição falharam.")
    return None

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    if not client or not model:
        say("Senhor, meu motor de inteligência não está disponível no momento.")
        return True

    say("Com certeza, Olair! Para qual canal devo criar esse vídeo? Diga Visão Milionária, Corpo de Titã, ou Fé Revelada.")
    canal = takeCommand()
    
    # Load profile for voice settings
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_path = os.path.join(base_dir, "profile.json")
    user_voice = "pt-BR-FranciscaNeural" # Fallback
    try:
        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
                user_voice = profile.get("voice", "pt-BR-FranciscaNeural")
    except Exception as e:
        print(f"[VideoExplicativo] Erro ao carregar profile.json: {e}")

    canal_id = "visao_milionaria"
    if canal and ("corpo" in canal.lower() or "titã" in canal.lower()):
        canal_id = "corpo_de_tita"
    elif canal and ("fé" in canal.lower() or "revelada" in canal.lower()):
        canal_id = "fe_revelada"
        
    config = load_channel_config(canal_id)
    if not config:
        config = {
            "nome": "Default",
            "nicho": "Geral",
            "cores_primarias": ["#FFC300", "#FCA311"],
            "cor_fundo_predominante": "#0D1321",
            "vibe": "Dark Premium com acento âmbar"
        }
        
    say(f"Entendido! Vou preparar o vídeo seguindo o estilo do canal {config['nome']}.")
    
    say("Para qual formato devo criar o vídeo? Diga Vertical para Shorts e TikTok, ou Horizontal para vídeos longos.")
    formato_raw = takeCommand()
    
    render_vertical = True
    render_horizontal = False
    
    if formato_raw:
        formato_lower = formato_raw.lower()
        if "horizontal" in formato_lower or "16:9" in formato_lower or "longo" in formato_lower:
            render_horizontal = True
            render_vertical = False
        if "ambos" in formato_lower or "dois" in formato_lower:
            render_horizontal = True
            render_vertical = True
            
    if render_vertical and not render_horizontal:
        say("Ótimo, focaremos apenas no formato Vertical 9 por 16.")
    elif render_horizontal and not render_vertical:
        say("Certo, focaremos apenas no formato Horizontal 16 por 9.")
    else:
        say("Preparando para renderizar em ambos os formatos.")
    
    # 1. Obtém o assunto do vídeo
    assunto = re.sub(r'laura|criar|crie|cria|gerar|gera|vídeo|vídeos|explicativo|sobre|fazer|faz|um|uma|inema', '', query.lower()).strip()
    if not assunto:
        assunto = "Mistérios da Bíblia"

    # Injeta o canal_id no config para uso interno no _build_script
    config['_canal_id'] = canal_id

    # Para o canal fe_revelada, busca versículos relevantes ao ASSUNTO específico
    if canal_id == "fe_revelada":
        try:
            from skills.bible_reference import get_bible_verse
        except ImportError:
            try:
                from bible_reference import get_bible_verse
            except ImportError:
                get_bible_verse = None

        if get_bible_verse:
            # Busca versículos que sejam relevantes ao tema do vídeo
            config['contexto_extra'] = _fetch_bible_verses_for_topic(assunto, canal_id)
            if config['contexto_extra']:
                print(f"[VideoExplicativo] Versículos carregados para o roteiro:\n{config['contexto_extra'][:300]}")

    project_slug = re.sub(r'[^a-z0-9]+', '_', assunto.lower()).strip('_')
    project_slug = project_slug[:30] # limita nome da pasta
    
    if not assunto or assunto == "none":
        say("Sem assunto definido, não consigo gerar o roteiro. Processo cancelado.")
        return True

    script_data = _build_script(client, model, assunto, config, render_vertical=render_vertical)
    if not script_data or "cenas" not in script_data or len(script_data["cenas"]) < 8:
        say("Tive um problema ao gerar um roteiro estruturado. Poderíamos tentar novamente?")
        return True

    # --- PASSO DE QA (CONTROLE DE QUALIDADE) ---
    try:
        from core.quality_controller import review_json_content
        # Passa as diretrizes específicas do canal para o Diretor de Criação
        formato_str = "VERTICAL (Shorts/TikTok — máx. 1 frase por cena, máx. 15 palavras por cena)" if render_vertical else "HORIZONTAL (Vídeo longo — 2 a 4 frases por cena)"
        channel_context = (
            f"Canal: {config['nome']}. Nicho: {config['nicho']}. "
            f"Vibe e Estética: {config['vibe']}. "
            f"Regras de Thumbnail: {config.get('regras_thumbnail', '')}. "
            f"FORMATO DO VÍDEO: {formato_str}. MANTENHA os textos dentro dos limites desse formato."
        )
        script_data = review_json_content(
            client, model, script_data,
            content_type=f"roteiro de vídeo curto viral para o canal {config['nome']} ({channel_context})"
        )
    except Exception as e:
        print(f"[VideoExplicativo] Erro ao instanciar Quality Controller: {e}")
    # -------------------------------------------

    # Interação para aprovação do roteiro
    say(f"Gerei um roteiro com o título: '{script_data.get('titulo', 'Vídeo Explicativo')}' contendo 8 cenas.")
    say(f"Aqui está a primeira cena de abertura: '{script_data['cenas'][0]['texto_original']}'")
    say("Senhor, aprova este roteiro para eu dar início às gravações de voz e animações?")
    
    confirmacao = takeCommand()
    if not confirmacao or not any(w in confirmacao.lower() for w in ["sim", "pode", "ok", "confirmo", "aprovado", "s"]):
        say("Entendido, Olair. Plano arquivado e processo interrompido.")
        return True

    say("Roteiro aprovado! Preparando a estrutura do projeto e gravando a locução local...")

    # 3. Criação de pastas do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.join(base_dir, "videos_criados", project_slug)
    
    assets_audio_dir = os.path.join(project_dir, "assets", "audio")
    assets_txt_dir = os.path.join(project_dir, "assets", "txt")
    assets_fonts_dir = os.path.join(project_dir, "assets", "fonts")
    renders_dir = os.path.join(project_dir, "renders")

    os.makedirs(assets_audio_dir, exist_ok=True)
    os.makedirs(assets_txt_dir, exist_ok=True)
    os.makedirs(assets_fonts_dir, exist_ok=True)
    os.makedirs(renders_dir, exist_ok=True)

    # 4. Geração de arquivos txt de narração
    for i, cena in enumerate(script_data["cenas"], 1):
        num = cena.get("numero", i)
        txt_path = os.path.join(assets_txt_dir, f"s{num}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(cena.get("texto_fala", ""))

    # Escrever cena 9 (CTA da MG Solution)
    cta_txt_path = os.path.join(assets_txt_dir, "s9.txt")
    with open(cta_txt_path, "w", encoding="utf-8") as f:
        f.write("Isso é conteúdo da MG Solution. Acesse: https://mg-solution.vercel.app")

    # 5. Locução via TTS
    say(f"Iniciando a geração da locução via {user_voice}. Isso pode levar alguns minutos...")

    # Pré-verificação: edge-tts disponível?
    edge_tts_available = False
    try:
        r_check = subprocess.run("edge-tts --version", shell=True, capture_output=True, text=True, timeout=5)
        edge_tts_available = (r_check.returncode == 0)
        if edge_tts_available:
            print("[VideoExplicativo] edge-tts detectado e disponivel.")
        else:
            print("[VideoExplicativo] edge-tts nao detectado. Continuando com Azure TTS como fallback.")
    except Exception:
        print("[VideoExplicativo] Falha ao verificar edge-tts. Continuando com Azure TTS como fallback.")

    # Azure Speech TTS como fallback
    azure_speech_key    = os.getenv("AZURE_SPEECH_KEY", "")
    azure_speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
    azure_tts_available = bool(azure_speech_key)

    tts_failed_scenes = []
    for i in range(1, 10):
        txt_abs = os.path.join(assets_txt_dir, f"s{i}.txt")
        wav_abs = os.path.join(assets_audio_dir, f"s{i}.wav")
        mp3_abs = os.path.join(assets_audio_dir, f"s{i}.mp3")
        txt_rel = os.path.relpath(txt_abs, project_dir)
        wav_rel = os.path.relpath(wav_abs, project_dir)
        mp3_rel = os.path.relpath(mp3_abs, project_dir)

        # Lê o texto para o fallback
        with open(txt_abs, "r", encoding="utf-8") as f:
            scene_text = f.read().strip()

        print(f"[VideoExplicativo] Gerando TTS para cena {i}...")
        tts_ok = False

        # --- Tentativa 1: edge-tts (principal) ---
        if not tts_ok and edge_tts_available:
            try:
                safe_text = scene_text.replace('"', "'")
                cmd_tts = f'edge-tts --voice {user_voice} --rate=-10% --pitch=-15Hz --text "{safe_text}" --write-media "{mp3_rel}"'
                r_tts = subprocess.run(cmd_tts, cwd=project_dir, shell=True,
                                       stdin=subprocess.DEVNULL,
                                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
                if r_tts.returncode == 0 and os.path.exists(mp3_abs):
                    cmd_conv = f'ffmpeg -y -i "{mp3_rel}" "{wav_rel}"'
                    r_conv = subprocess.run(cmd_conv, cwd=project_dir, shell=True,
                                            stdin=subprocess.DEVNULL,
                                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
                    if r_conv.returncode == 0 and os.path.exists(wav_abs):
                        tts_ok = True
                        print(f"[VideoExplicativo] Cena {i} gerada via edge-tts.")
                    else:
                        tts_ok = os.path.exists(mp3_abs)
                        print(f"[VideoExplicativo] Cena {i}: conversao WAV falhou, usando MP3 para duracao.")
                else:
                    print(f"[VideoExplicativo] edge-tts falhou na cena {i}: {r_tts.stderr[:200]}")
            except Exception as e:
                print(f"[VideoExplicativo] Erro no edge-tts cena {i}: {e}")

        # --- Tentativa 2: Azure Speech TTS (fallback — 500k chars/mês grátis, vozes PT-BR nativas) ---
        if not tts_ok and azure_tts_available:
            try:
                import requests as _req_az
                # Voz padrão para vídeos: DonatoNeural (grave, autoritária — ótima para narração)
                azure_voice = os.getenv("AZURE_TTS_VOICE", "pt-BR-DonatoNeural")
                ssml = (
                    f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">'
                    f'<voice name="{azure_voice}">{scene_text}</voice>'
                    f'</speak>'
                )
                az_url = f"https://{azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
                az_headers = {
                    "Ocp-Apim-Subscription-Key": azure_speech_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
                }
                r_az = _req_az.post(az_url, headers=az_headers, data=ssml.encode("utf-8"), timeout=30)
                if r_az.status_code == 200:
                    with open(mp3_abs, "wb") as af:
                        af.write(r_az.content)
                    cmd_conv_az = f'ffmpeg -y -i "{mp3_rel}" "{wav_rel}"'
                    subprocess.run(cmd_conv_az, cwd=project_dir, shell=True,
                                   stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
                    tts_ok = os.path.exists(wav_abs) or os.path.exists(mp3_abs)
                    if tts_ok:
                        print(f"[VideoExplicativo] Cena {i} gerada via Azure Speech TTS ({azure_voice}).")
                else:
                    print(f"[VideoExplicativo] Azure TTS falhou na cena {i}: HTTP {r_az.status_code} - {r_az.text[:200]}")
            except Exception as e:
                print(f"[VideoExplicativo] Erro no Azure TTS cena {i}: {e}")

        if not tts_ok:
            tts_failed_scenes.append(i)
            print(f"[VideoExplicativo] TTS falhou para cena {i} em todas as tentativas. Duração padrão de 5s.")

    if tts_failed_scenes:
        say(f"Aviso: geração de voz falhou em {len(tts_failed_scenes)} cenas ({', '.join(f'cena {c}' for c in tts_failed_scenes)}). Continuando com duração padrão.")


    # 6. Cálculo das durações dos áudios
    audio_durations = []
    for i in range(1, 10):
        wav_path = os.path.join(assets_audio_dir, f"s{i}.wav")
        mp3_path = os.path.join(assets_audio_dir, f"s{i}.mp3")
        # Prioriza WAV; fallback para MP3 se existir
        if os.path.exists(wav_path):
            dur = get_audio_duration(wav_path)
        elif os.path.exists(mp3_path):
            dur = get_audio_duration(mp3_path)
        else:
            dur = 5.0
        audio_durations.append(dur)

    print(f"[VideoExplicativo] Durações medidas: {audio_durations}")

    # 7. Geração da composição visual (HTML/GSAP)
    comp_data = _generate_composition_code(client, model, script_data, config)
    if not comp_data or "scenes" not in comp_data or "animations" not in comp_data:
        say("Desculpe senhor, ocorreu um erro ao gerar o design visual e as animações com a IA. Vamos abortar.")
        return True

    # 8. Montagem do build-index.mjs
    say("Locução pronta e durações calculadas. Construindo a timeline de motion design...")

    # Formatar scene functions
    scene_functions_str = ""
    for i in range(1, 9):
        func_body = comp_data["scenes"].get(f"scene{i}", "")
        # Remove qualquer 'return' ou crases existentes para normalizar o conteúdo
        func_body = func_body.replace("return", "").strip()
        func_body = func_body.replace("`", "\\`").replace("${", "\\${")

        # Re-insere o conteúdo de forma segura em um template literal
        # Usamos aspas simples para a função e crases para o HTML
        scene_functions_str += f"function scene{i}() {{\n  return `{func_body}`;\n}}\n"

    # Formatar cases de animação
    anim_cases_str = ""
    for i in range(1, 9):
        case_body = comp_data["animations"].get(str(i), "")
        # Sanitiza backticks nos códigos de animação
        case_body = case_body.replace("`", "\\`").replace("${", "\\${")
        anim_cases_str += f"    case {i}:\n      P(`{case_body}`);\n      break;\n"

    # Extrair Captions
    captions = [cena.get("caption", "Vídeo Explicativo") for cena in script_data["cenas"]]
    # Adicionar legenda da CTA
    captions.append("Mais conteúdo em inema.club")

    # -----------------------------------------------------------------------
    # 8.A BUSCA DE ASSETS DE MÍDIA (Fotos/Vídeo global + Trilha Sonora)
    # -----------------------------------------------------------------------
    bg_photo_css = ""
    bg_video_path = None
    bg_video_tag = ""
    soundtrack_path = None
    scene_bg_urls = {}   # {cena_num: url_local_ou_remota}
    scene_bg_types = {}  # {cena_num: "photo"|"video"}

    if _assets_available:
        say("Buscando recursos visuais e sonoros para o vídeo...")
        import requests as _req
        import random as _rand

        assets_bg_dir = os.path.join(project_dir, "assets", "bg_scenes")
        os.makedirs(assets_bg_dir, exist_ok=True)

        # -----------------------------------------------------------------------
        # 8.A.1 BUSCA DE ASSETS VISUAIS POR CENA (imagem/vídeo único por cena)
        # -----------------------------------------------------------------------
        say("Buscando imagens de fundo únicas para cada cena do vídeo...")
        print("[VideoExplicativo] Iniciando busca de backgrounds por cena...")

        try:
            from skills.visual_assets import search_pexels_videos, search_pixabay_videos, get_best_photo
        except ImportError:
            from visual_assets import search_pexels_videos, search_pixabay_videos, get_best_photo

        cenas_roteiro = script_data.get("cenas", [])

        for idx_c, cena in enumerate(cenas_roteiro):
            cena_num = cena.get("numero", idx_c + 1)
            visual_desc = cena.get("visual_desc", "")
            titulo_cena = cena.get("titulo_cena", "")

            # Monta keyword: visual_desc tem prioridade
            if visual_desc and len(visual_desc.strip()) > 5:
                kw_clean = re.sub(
                    r'\b(com|uma|um|de|do|da|e|a|o|em|para|que|se|no|na|glow|âmbar|amber)\b',
                    ' ', visual_desc.lower(), flags=re.IGNORECASE
                ).strip()
                kw_clean = re.sub(r'\s+', ' ', kw_clean).strip()[:60]
            else:
                kw_clean = f"{assunto} {titulo_cena}"[:60]

            # Adiciona contexto do nicho do canal para melhorar relevância
            nicho = config.get('nicho', '')
            search_kw = f"{kw_clean} {nicho}"[:80] if nicho and nicho.lower() not in kw_clean.lower() else kw_clean

            print(f"[VideoExplicativo] Cena {cena_num} — buscando para: '{search_kw}'")

            found_url = None
            found_type = None

            # Tenta vídeo B-roll primeiro
            videos = search_pexels_videos(search_kw, per_page=5)
            if not videos:
                videos = search_pexels_videos(assunto, per_page=5)
            if not videos:
                videos = search_pixabay_videos(search_kw, per_page=5)

            if videos:
                chosen = _rand.choice(videos)
                video_url = chosen.get("url", "")
                if video_url:
                    local_name = f"bg_s{cena_num}.mp4"
                    local_path = os.path.join(assets_bg_dir, local_name)
                    temp_vpath = os.path.join(assets_bg_dir, f"tmp_s{cena_num}.mp4")
                    try:
                        rv = _req.get(video_url, timeout=45, stream=True)
                        rv.raise_for_status()
                        with open(temp_vpath, "wb") as vf2:
                            for chunk in rv.iter_content(8192):
                                vf2.write(chunk)
                        cmd_lp = f'ffmpeg -y -stream_loop -1 -i "{temp_vpath}" -t 30 -c copy "{local_path}"'
                        subprocess.run(cmd_lp, shell=True, capture_output=True, timeout=60)
                        try:
                            os.remove(temp_vpath)
                        except Exception:
                            pass
                        if os.path.exists(local_path):
                            found_url = f"assets/bg_scenes/{local_name}"
                            found_type = "video"
                            print(f"[VideoExplicativo] Cena {cena_num}: vídeo baixado ({local_name})")
                    except Exception as e:
                        print(f"[VideoExplicativo] Erro vídeo cena {cena_num}: {e}")

            # Fallback: foto estática por cena
            if not found_url:
                photo_c = get_best_photo(search_kw)
                if not photo_c:
                    photo_c = get_best_photo(assunto)
                if photo_c:
                    found_url = photo_c.get("url_large", "")
                    found_type = "photo"
                    print(f"[VideoExplicativo] Cena {cena_num}: foto remota: {found_url[:60]}...")

            if found_url:
                scene_bg_urls[cena_num] = found_url
                scene_bg_types[cena_num] = found_type

        print(f"[VideoExplicativo] Backgrounds por cena: {len(scene_bg_urls)}/8 coletados")
        say(f"Backgrounds visuais: {len(scene_bg_urls)} imagens únicas coletadas para as cenas.")

        # -----------------------------------------------------------------------
        # 8.A.2 TRILHA SONORA
        # -----------------------------------------------------------------------
        canal_mood_map = {
            "visao_milionaria": "motivational epic",
            "corpo_de_tita":    "energetic powerful",
            "fe_revelada":      "epic cinematic sacred"
        }
        mood_tag = canal_mood_map.get(canal_id, "cinematic ambient")
        print(f"[VideoExplicativo] Buscando trilha sonora para mood: '{mood_tag}'")
        audio_track = get_best_audio(mood_tag)
        if audio_track and audio_track.get("local_path"):
            soundtrack_dest = os.path.join(project_dir, "assets", "audio", "soundtrack.mp3")
            try:
                cmd_vol = f'ffmpeg -y -i "{audio_track["local_path"]}" -filter:a "volume=0.08" "{soundtrack_dest}"'
                subprocess.run(cmd_vol, shell=True, capture_output=True)
                soundtrack_path = "assets/audio/soundtrack.mp3"
                print(f"[VideoExplicativo] Trilha: {audio_track.get('name')} - {audio_track.get('artist')}")
                say(f"Trilha sonora: {audio_track.get('name')} do artista {audio_track.get('artist')}.")
            except Exception as e:
                print(f"[VideoExplicativo] Falha ao processar trilha: {e}")
        else:
            print("[VideoExplicativo] Nenhuma trilha sonora encontrada via Jamendo.")
    else:
        print("[VideoExplicativo] Assets desativados — sem foto, vídeo ou trilha.")

    # -----------------------------------------------------------------------
    # 8.B CONSTRUÇÃO DOS BACKGROUNDS DE CENA NO TEMPLATE HTML
    # -----------------------------------------------------------------------
    # Estratégia: cada cena recebe um bloco CSS com background-image direto.
    # Isso funciona corretamente com o Hyperframes (renderizador headless)
    # porque não depende de JS ou eventos de scroll para ativar o background.
    scene_bg_css_rules = ""
    scene_bg_html_blocks = ""
    scene_bg_switch_script = ""  # Não é mais necessário JS para troca

    if scene_bg_urls:
        css_rules = []
        # CSS base para o bg-media que contém os backgrounds
        css_rules.append("""
      /* ---- backgrounds por cena --- */
      .scene-bg{
        position:absolute;inset:0;z-index:1;pointer-events:none;
        background-size:cover;background-position:center center;
        background-repeat:no-repeat;
      }
      .scene-bg::after{
        content:'';position:absolute;inset:0;
        background:rgba(0,0,0,0.50);z-index:1;
      }
      .scene-bg video,.scene-bg img{
        position:absolute;inset:0;width:100%;height:100%;
        object-fit:cover;z-index:0;
      }""")

        # Gera CSS específico por cena: cada #s{N} .scene-bg terá sua imagem
        for cena_num, url in scene_bg_urls.items():
            bg_type = scene_bg_types.get(cena_num, "photo")
            if bg_type == "photo":
                # Para fotos: usa background-image no CSS diretamente
                css_rules.append(f"      #scene-bg-{cena_num}{{background-image:url('{url}')}}")

        scene_bg_css_rules = "\n".join(css_rules)

        # Gera o HTML dos divs de background (um por cena)
        for cena_num, url in scene_bg_urls.items():
            bg_type = scene_bg_types.get(cena_num, "photo")
            if bg_type == "video":
                # Para vídeos: usa tag <video> dentro do div
                inner = (
                    f'<video autoplay muted loop playsinline '
                    f'style="position:absolute;inset:0;width:100%;height:100%;'
                    f'object-fit:cover;z-index:0;">'
                    f'<source src="{url}" type="video/mp4"></video>'
                    f'<div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div>'
                )
            else:
                # Para fotos: a imagem já está no CSS via background-image
                inner = '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div>'

            scene_bg_html_blocks += (
                f'\n      <div class="scene-bg" id="scene-bg-{cena_num}">'
                f'{inner}</div>'
            )

        # Script mínimo: apenas associa cada scene-bg à sua cena via GSAP
        # Cada scene-bg fica dentro do #bg-media e é absolutamente posicionado.
        # A visibilidade é controlada pelo GSAP junto com a cena correspondente.
        bg_gsap_lines = []
        for cena_num in sorted(scene_bg_urls.keys()):
            s_idx = cena_num - 1  # índice da cena (0-based) no array S
            # Oculta todos os bgs no início, depois mostra o correto no tempo da cena
            bg_gsap_lines.append(
                f"        gsap.set('#scene-bg-{cena_num}', {{opacity: 0}});"
            )
        # Ativa o primeiro bg imediatamente
        if scene_bg_urls:
            first = min(scene_bg_urls.keys())
            bg_gsap_lines.append(f"        gsap.set('#scene-bg-{first}', {{opacity: 1}});")

        # Para cada cena, adiciona tween no GSAP para trocar o bg no tempo correto
        # O script de troca é simples: usa gsap.to na timeline principal
        scene_nums_sorted = sorted(scene_bg_urls.keys())
        for i, cena_num in enumerate(scene_nums_sorted):
            next_num = scene_nums_sorted[i + 1] if i + 1 < len(scene_nums_sorted) else None
            # O timing é calculado com base no índice da cena
            # S[cena_num-1].start é o tempo de início, mas no JS é via S array
            # Usamos uma abordagem mais simples: o script é injetado após a timeline GSAP
            if next_num:
                bg_gsap_lines.append(
                    f"        // bg cena {cena_num} -> {next_num}"
                )

        scene_bg_switch_script = (
            "\n        // ---- Backgrounds por cena via GSAP ----\n"
            + "\n".join(bg_gsap_lines)
            + "\n"
            + "        // Liga IntersectionObserver para troca suave\n"
            + "        (function() {\n"
            + "          const bgIds = {"
            + ", ".join(f"{n}: 'scene-bg-{n}'" for n in sorted(scene_bg_urls.keys()))
            + "};\n"
            + "          function activateBg(n) {\n"
            + "            Object.values(bgIds).forEach(id => {\n"
            + "              const el = document.getElementById(id);\n"
            + "              if (el) el.style.opacity = '0';\n"
            + "            });\n"
            + "            const t = document.getElementById(bgIds[n]);\n"
            + "            if (t) t.style.opacity = '1';\n"
            + "          }\n"
            + "          activateBg(" + str(min(scene_bg_urls.keys())) + ");\n"
            + "          const obs = new IntersectionObserver(function(entries) {\n"
            + "            entries.forEach(function(e) {\n"
            + "              if (e.isIntersecting) {\n"
            + "                const si = parseInt(e.target.id.replace('s',''));\n"
            + "                if (bgIds[si] !== undefined) activateBg(si);\n"
            + "              }\n"
            + "            });\n"
            + "          }, {threshold: 0.3, root: document.getElementById('root')});\n"
            + "          document.querySelectorAll('.scene').forEach(s => obs.observe(s));\n"
            + "        })();\n"
        )

    # Injetar variáveis no template
    mjs_code = COMPOSITION_TEMPLATE_CODE
    mjs_code = mjs_code.replace("/*_AUDIO_DURATIONS_*/", ", ".join(map(str, audio_durations)))
    mjs_code = mjs_code.replace("/*_CAPTIONS_*/", json.dumps(captions, ensure_ascii=False))
    mjs_code = mjs_code.replace("/*_SCENE_FUNCTIONS_*/", scene_functions_str)
    mjs_code = mjs_code.replace("/*_ANIMATION_CASES_*/", anim_cases_str)

    # Injeções de cores do canal configurado
    c_bg = config.get("cor_fundo_predominante", "#0D1321")
    c_acc = config["cores_primarias"][0]
    c_acc2 = config["cores_primarias"][1] if len(config["cores_primarias"]) > 1 else c_acc
    
    mjs_code = mjs_code.replace("/*_VAR_BG_*/", c_bg)
    mjs_code = mjs_code.replace("/*_VAR_BG2_*/", "#1D2D44")
    mjs_code = mjs_code.replace("/*_VAR_BG3_*/", "#3E5C76")
    mjs_code = mjs_code.replace("/*_VAR_FG_*/", "#F0EBD8")
    mjs_code = mjs_code.replace("/*_VAR_ACCENT_*/", c_acc)
    mjs_code = mjs_code.replace("/*_VAR_ACCENT2_*/", c_acc2)
    mjs_code = mjs_code.replace("/*_VAR_ACCENT_RGB_*/", hex_to_rgb_str(c_acc))

    # Injeção do vídeo/foto de fundo nos backgrounds do HTML
    mjs_code = mjs_code.replace("/*_BG_VIDEO_TAG_*/", bg_video_tag)
    mjs_code = mjs_code.replace("/*_BG_PHOTO_CSS_*/", bg_photo_css)

    # Injeção dos backgrounds por cena (CSS + HTML + script JS)
    mjs_code = mjs_code.replace("/*_SCENE_BG_CSS_*/", scene_bg_css_rules)
    mjs_code = mjs_code.replace("/*_SCENE_BG_HTML_*/", scene_bg_html_blocks)
    mjs_code = mjs_code.replace("/*_SCENE_BG_SCRIPT_*/", scene_bg_switch_script)

    # Injeção da trilha sonora (audio element)
    soundtrack_tag = ""
    if soundtrack_path:
        soundtrack_tag = f'<audio id="soundtrack" src="{soundtrack_path}" loop style="display:none"></audio>'
    mjs_code = mjs_code.replace("/*_SOUNDTRACK_TAG_*/", soundtrack_tag)

    # Injeção do ghost text (palavra principal do assunto, em maiúsculas, sem acentos)
    ghost_words = re.sub(r'[^a-zA-Z0-9\s]', '', assunto.upper()).split()
    ghost_text = ghost_words[0] if ghost_words else config.get("nome", "LAURA").upper()
    mjs_code = mjs_code.replace("/*_GHOST_TEXT_*/", ghost_text)

    build_index_path = os.path.join(project_dir, "build-index.mjs")
    with open(build_index_path, "w", encoding="utf-8") as f:
        f.write(mjs_code)

    # Escrever script de fontes
    fetch_fonts_path = os.path.join(project_dir, "fetch-fonts.mjs")
    with open(fetch_fonts_path, "w", encoding="utf-8") as f:
        f.write(FETCH_FONTS_CODE)
    
    # 9. Preparação de ambiente
    say("Configurando ambiente e fontes tipográficas...")

    # Verifica fontes
    try:
        subprocess.run("node fetch-fonts.mjs", cwd=project_dir, shell=True,
                       stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception as e:
        print(f"[VideoExplicativo] Aviso ao baixar fontes: {e}")
        say("Aviso: Falha ao baixar fontes automaticamente. O sistema continuará com fontes padrão.")

    # Verifica FFmpeg usando shell (mesmo PATH do terminal do usuário)
    ffmpeg_ok = False
    try:
        r_ffmpeg = subprocess.run("ffmpeg -version", shell=True, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        ffmpeg_ok = (r_ffmpeg.returncode == 0)
    except Exception:
        ffmpeg_ok = bool(shutil.which("ffmpeg"))

    if not ffmpeg_ok:
        print("[VideoExplicativo] Aviso: ffmpeg não detectado via shell. A renderização pode falhar.")
        say("Aviso: não consegui detectar o FFmpeg, mas vou tentar renderizar mesmo assim.")

    # 10. Renderização final dos vídeos
    say("Tudo pronto! Iniciando a renderização final do vídeo...")

    success_16x9 = False
    success_9x16 = False
    output_16x9_abs = ""
    output_9x16_abs = ""

    # --- 16:9 (Horizontal) ---
    if render_horizontal:
        say("Renderizando formato horizontal 16x9...")
        
        # Compila o index.html horizontal
        print("[VideoExplicativo] Compilando index.html horizontal...")
        try:
            res_build = subprocess.run("node build-index.mjs", cwd=project_dir, shell=True,
                                       stdin=subprocess.DEVNULL,
                                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            if res_build.returncode != 0:
                print(f"[VideoExplicativo] Erro ao compilar index.html (horizontal): {res_build.stderr}")
                say("Erro técnico ao compilar a estrutura visual do vídeo horizontal.")
            else:
                output_16x9 = f"renders/{project_slug}-16x9.mp4"
                output_16x9_abs = os.path.join(project_dir, output_16x9)
                result_render1 = subprocess.run(
                    f'npx -y hyperframes render --quality standard --fps 24 --resolution landscape --page-side-compositing --output "{output_16x9}"',
                    cwd=project_dir, shell=True,
                    stdin=subprocess.DEVNULL,   # Evita hang aguardando teclado
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900
                )
                if result_render1.returncode != 0:
                    print(f"[VideoExplicativo] Erro ao renderizar 16:9:\nSTDOUT: {result_render1.stdout[-500:]}\nSTDERR: {result_render1.stderr[-500:]}")
                    say(f"A renderização do formato 16:9 falhou.")
                else:
                    success_16x9 = os.path.exists(output_16x9_abs)
        except Exception as e:
            print(f"[VideoExplicativo] Exceção na renderização 16:9: {e}")
            say("Ocorreu um erro crítico ao tentar renderizar o vídeo horizontal.")

    # --- 9:16 (Vertical) ---
    if render_vertical:
        say("Renderizando formato vertical 9x16...")
        
        # Regera o index.html em modo vertical
        print("[VideoExplicativo] Compilando index.html vertical...")
        try:
            res_build_v = subprocess.run("node build-index.mjs --vertical", cwd=project_dir, shell=True,
                                        stdin=subprocess.DEVNULL,
                                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            if res_build_v.returncode != 0:
                print(f"[VideoExplicativo] Erro ao compilar index vertical: {res_build_v.stderr}")
                say("Aviso: Não foi possível compilar a versão vertical do design.")
            else:
                output_9x16 = f"renders/{project_slug}-9x16.mp4"
                output_9x16_abs = os.path.join(project_dir, output_9x16)
                result_render2 = subprocess.run(
                    f'npx -y hyperframes render --quality standard --fps 24 --resolution portrait --page-side-compositing --output "{output_9x16}"',
                    cwd=project_dir, shell=True,
                    stdin=subprocess.DEVNULL,   # Evita hang aguardando teclado
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900
                )
                if result_render2.returncode != 0:
                    print(f"[VideoExplicativo] Erro ao renderizar 9:16:\nSTDOUT: {result_render2.stdout[-500:]}\nSTDERR: {result_render2.stderr[-500:]}")
                    say(f"A renderização do formato 9:16 falhou.")
                else:
                    success_9x16 = os.path.exists(output_9x16_abs)
        except Exception as e:
            print(f"[VideoExplicativo] Exceção na renderização 9:16: {e}")
            say("Ocorreu um erro crítico ao tentar renderizar o vídeo vertical.")

    # Verificação final de arquivos
    renderizou_algum = success_16x9 or success_9x16

    if not renderizou_algum:
        say("Senhor, infelizmente a renderização falhou. Verifique os logs do hyperframes.")
        return True

    if render_horizontal and render_vertical:
        if success_16x9 and success_9x16:
            say("Excelente! Seus vídeos foram renderizados com sucesso nos formatos horizontal e vertical.")
        else:
            say("Os vídeos foram gerados, mas um dos formatos falhou.")
    else:
        say("Excelente! Seu vídeo foi renderizado com sucesso no formato escolhido.")

    say("Abrindo a pasta contendo as mídias finais, senhor.")
    
    absolute_renders_path = os.path.abspath(renders_dir)
    webbrowser.open(f"file:///{absolute_renders_path.replace(os.sep, '/')}")
    return True
