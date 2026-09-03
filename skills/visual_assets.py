import os
import sys
import json
import requests
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    from core.rate_limiter import can_request, register_request, get_cached, set_cached
    _rl_available = True
except ImportError:
    _rl_available = False
    def can_request(api, say_callback=None): return True
    def register_request(api): pass
    def get_cached(api, params): return None
    def set_cached(api, params, data): pass

KEYWORDS = [
    "buscar imagem", "buscar foto", "encontrar foto", "foto profissional",
    "imagem para", "foto para vídeo", "foto para site", "foto para post",
    "unsplash", "pexels", "banco de imagens", "stock photo",
    "foto de fundo", "background image", "b-roll", "vídeo de fundo",
    "paleta de cores", "gerar paleta", "esquema de cores", "colormind",
    "ícones para", "buscar ícone",
    # Status de cotas
    "cota das apis", "limite das apis", "uso das apis", "quantas requisições"
]


# --- PATHS ---
ASSETS_DIR = os.path.join(BASE_DIR, "assets_baixados")
os.makedirs(ASSETS_DIR, exist_ok=True)


# =============================================================================
#  PEXELS API (Fotos + Vídeos gratuitos — 200 req/hora)
# =============================================================================

def search_pexels_photos(query, per_page=5, orientation="landscape"):
    """Busca fotos profissionais na Pexels. Retorna lista de dicts com url, photographer, alt."""
    api_key = os.getenv("PEXELS_API_KEY", "")
    if not api_key:
        print("[VisualAssets] PEXELS_API_KEY não configurada no .env")
        return []

    cache_params = {"q": query, "n": per_page, "o": orientation}

    # 1. Verifica cache antes de tudo
    cached = get_cached("pexels", cache_params)
    if cached is not None:
        return cached

    # 2. Verifica se ainda temos cota disponível
    if not can_request("pexels"):
        return []

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "orientation": orientation}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        register_request("pexels")  # Contabiliza após sucesso
        data = response.json()
        results = []
        for photo in data.get("photos", []):
            results.append({
                "id": photo["id"],
                "url_large": photo["src"]["large2x"],
                "url_medium": photo["src"]["medium"],
                "url_original": photo["src"]["original"],
                "photographer": photo["photographer"],
                "alt": photo.get("alt", ""),
                "source": "pexels"
            })
        set_cached("pexels", cache_params, results)  # Armazena no cache
        return results
    except Exception as e:
        print(f"[VisualAssets] Erro Pexels Photos: {e}")
        return []


def search_pexels_videos(query, per_page=3, orientation="landscape"):
    """Busca vídeos B-roll gratuitos na Pexels."""
    api_key = os.getenv("PEXELS_API_KEY", "")
    if not api_key:
        print("[VisualAssets] PEXELS_API_KEY não configurada no .env")
        return []

    cache_params = {"type": "video", "q": query, "n": per_page, "o": orientation}

    # 1. Verifica cache
    cached = get_cached("pexels", cache_params)
    if cached is not None:
        return cached

    # 2. Verifica cota
    if not can_request("pexels"):
        return []

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "orientation": orientation}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        register_request("pexels")  # Contabiliza após sucesso
        data = response.json()
        results = []
        for video in data.get("videos", []):
            best_file = None
            for vf in video.get("video_files", []):
                if vf.get("quality") == "hd":
                    best_file = vf
                    break
            if not best_file and video.get("video_files"):
                best_file = video["video_files"][0]

            if best_file:
                results.append({
                    "id": video["id"],
                    "url": best_file["link"],
                    "width": best_file.get("width"),
                    "height": best_file.get("height"),
                    "duration": video.get("duration"),
                    "source": "pexels_video"
                })
        set_cached("pexels", cache_params, results)
        return results
    except Exception as e:
        print(f"[VisualAssets] Erro Pexels Videos: {e}")
        return []


# =============================================================================
#  UNSPLASH API (Fotos HD — 50 req/hora no free tier)
# =============================================================================

def search_unsplash_photos(query, per_page=5, orientation="landscape"):
    """Busca fotos profissionais no Unsplash."""
    api_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
    if not api_key:
        print("[VisualAssets] UNSPLASH_ACCESS_KEY não configurada no .env")
        return []

    cache_params = {"src": "unsplash", "q": query, "n": per_page, "o": orientation}

    # 1. Verifica cache (Unsplash tem limite mais apertado: 50/hora)
    cached = get_cached("unsplash", cache_params)
    if cached is not None:
        return cached

    # 2. Verifica cota
    if not can_request("unsplash"):
        return []

    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {api_key}"}
    params = {"query": query, "per_page": per_page, "orientation": orientation}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        register_request("unsplash")  # Contabiliza após sucesso
        data = response.json()
        results = []
        for photo in data.get("results", []):
            results.append({
                "id": photo["id"],
                "url_large": photo["urls"]["regular"],
                "url_medium": photo["urls"]["small"],
                "url_original": photo["urls"]["full"],
                "photographer": photo["user"]["name"],
                "alt": photo.get("alt_description", ""),
                "source": "unsplash"
            })
        set_cached("unsplash", cache_params, results)
        return results
    except Exception as e:
        print(f"[VisualAssets] Erro Unsplash: {e}")
        return []


# =============================================================================
#  PIXABAY API (Fotos e Vídeos Gratuitos)
# =============================================================================

def search_pixabay_photos(query, per_page=5, orientation="horizontal"):
    """Busca fotos e ilustrações gratuitas no Pixabay."""
    api_key = os.getenv("PIXABAY_API_KEY", "")
    if not api_key:
        print("[VisualAssets] PIXABAY_API_KEY não configurada no .env")
        return []

    if orientation == "landscape":
        orientation = "horizontal"

    cache_params = {"src": "pixabay", "type": "photo", "q": query, "n": per_page, "o": orientation}

    # 1. Verifica cache
    cached = get_cached("pixabay", cache_params)
    if cached is not None:
        return cached

    # 2. Verifica cota
    if not can_request("pixabay"):
        return []

    url = "https://pixabay.com/api/"
    params = {"key": api_key, "q": query, "per_page": per_page, "orientation": orientation, "image_type": "photo"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        register_request("pixabay")  # Contabiliza após sucesso
        data = response.json()
        results = []
        for photo in data.get("hits", []):
            results.append({
                "id": photo["id"],
                "url_large": photo.get("largeImageURL", photo.get("webformatURL")),
                "url_medium": photo.get("webformatURL"),
                "url_original": photo.get("imageURL", photo.get("largeImageURL")),
                "photographer": photo.get("user", "Pixabay"),
                "alt": photo.get("tags", ""),
                "source": "pixabay"
            })
        set_cached("pixabay", cache_params, results)
        return results
    except Exception as e:
        print(f"[VisualAssets] Erro Pixabay Photos: {e}")
        return []


def search_pixabay_videos(query, per_page=3):
    """Busca vídeos B-roll no Pixabay."""
    api_key = os.getenv("PIXABAY_API_KEY", "")
    if not api_key:
        print("[VisualAssets] PIXABAY_API_KEY não configurada no .env")
        return []

    cache_params = {"src": "pixabay", "type": "video", "q": query, "n": per_page}

    cached = get_cached("pixabay", cache_params)
    if cached is not None:
        return cached

    if not can_request("pixabay"):
        return []

    url = "https://pixabay.com/api/videos/"
    params = {"key": api_key, "q": query, "per_page": per_page}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        register_request("pixabay")
        data = response.json()
        results = []
        for video in data.get("hits", []):
            videos_formats = video.get("videos", {})
            best_file = videos_formats.get("large") or videos_formats.get("medium") or videos_formats.get("small")
            
            if best_file and best_file.get("url"):
                results.append({
                    "id": video["id"],
                    "url": best_file["url"],
                    "width": best_file.get("width"),
                    "height": best_file.get("height"),
                    "duration": video.get("duration"),
                    "source": "pixabay_video"
                })
        set_cached("pixabay", cache_params, results)
        return results
    except Exception as e:
        print(f"[VisualAssets] Erro Pixabay Videos: {e}")
        return []


# =============================================================================
#  PINTEREST API (Busca de Pins com imagens inspiracionais)
# =============================================================================

def search_pinterest_pins(query, bookmark=None):
    """
    Busca pins no Pinterest usando a API v5.
    Retorna lista de dicts com url da imagem, título e descrição.
    NOTA: Requer que o PINTEREST_API_KEY seja um Access Token válido (OAuth2).
    """
    api_key = os.getenv("PINTEREST_API_KEY", "")
    if not api_key:
        print("[VisualAssets] PINTEREST_API_KEY não configurada no .env")
        return []

    cache_params = {"src": "pinterest", "q": query}
    cached = get_cached("pinterest", cache_params)
    if cached is not None:
        return cached

    if not can_request("pinterest"):
        return []

    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {"query": query, "page_size": 5}
    if bookmark:
        params["bookmark"] = bookmark

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        register_request("pinterest")
        data = response.json()
        results = []
        for pin in data.get("items", []):
            media = pin.get("media", {})
            images = media.get("images", {})
            # Pega a maior resolução disponível
            img_url = None
            for size_key in ["1200x", "736x", "600x", "400x", "236x"]:
                if size_key in images:
                    img_url = images[size_key].get("url")
                    break
            if img_url:
                results.append({
                    "id": pin.get("id"),
                    "url_large": img_url,
                    "url_medium": img_url,
                    "url_original": img_url,
                    "photographer": "Pinterest",
                    "alt": pin.get("title", "") or pin.get("description", ""),
                    "source": "pinterest"
                })
        set_cached("pinterest", cache_params, results)
        return results
    except Exception as e:
        print(f"[VisualAssets] Erro Pinterest: {e}")
        return []


# =============================================================================
#  COLORMIND API (Paletas de Cores — Sem chave, 100% gratuita)
# =============================================================================

def generate_color_palette(seed_color=None):
    """Gera uma paleta de 5 cores harmônicas usando Colormind."""
    url = "http://colormind.io/api/"
    body = {"model": "default"}

    if seed_color:
        # seed_color deve ser [R, G, B] ex: [255, 195, 0]
        body["input"] = [seed_color, "N", "N", "N", "N"]

    try:
        response = requests.post(url, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()
        colors = data.get("result", [])
        hex_colors = []
        for rgb in colors:
            hex_color = "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
            hex_colors.append(hex_color)
        return hex_colors
    except Exception as e:
        print(f"[VisualAssets] Erro Colormind: {e}")
        return []


# =============================================================================
#  DOWNLOAD DE ASSETS
# =============================================================================

def download_asset(url, filename, subfolder="photos"):
    """Baixa um asset (foto ou vídeo) para a pasta local."""
    target_dir = os.path.join(ASSETS_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[VisualAssets] Asset salvo: {filepath}")
        return filepath
    except Exception as e:
        print(f"[VisualAssets] Erro no download: {e}")
        return None


# =============================================================================
#  FUNÇÕES UTILITÁRIAS (Para outros módulos importarem)
# =============================================================================

def get_best_photo(keyword, orientation="landscape"):
    """
    Busca a melhor foto disponível. Tenta Pexels primeiro, depois Unsplash, Pixabay e Pinterest.
    Retorna dict com url_large, photographer e source, ou None.
    Pode ser chamada por: video_explicativo.py, web_page_creator.py, etc.
    """
    # Filtro de qualidade automático (cinematic, high quality)
    aesthetic_keyword = f"{keyword} cinematic high quality dark"

    # Tenta Pexels (maior limite de requisições)
    results = search_pexels_photos(aesthetic_keyword, per_page=1, orientation=orientation)
    if not results:
        # Tenta sem o filtro dark se não achar nada
        results = search_pexels_photos(keyword, per_page=1, orientation=orientation)

    if results:
        return results[0]

    # Fallback 1: Unsplash
    results = search_unsplash_photos(aesthetic_keyword, per_page=1, orientation=orientation)
    if not results:
        results = search_unsplash_photos(keyword, per_page=1, orientation=orientation)

    if results:
        return results[0]
        
    # Fallback 2: Pixabay
    results = search_pixabay_photos(keyword, per_page=1, orientation=orientation)
    if results:
        return results[0]

    # Fallback 3: Pinterest
    results = search_pinterest_pins(keyword)
    if results:
        return results[0]

    return None


def get_best_video(keyword, orientation="landscape"):
    """
    Busca o melhor vídeo B-roll disponível (Pexels, depois Pixabay).
    Retorna dict com url, width, height, duration, ou None.
    """
    aesthetic_keyword = f"{keyword} cinematic 4k"
    results = search_pexels_videos(aesthetic_keyword, per_page=1, orientation=orientation)
    if not results:
        results = search_pexels_videos(keyword, per_page=1, orientation=orientation)
        
    if results:
        return results[0]
        
    # Fallback Pixabay
    results = search_pixabay_videos(keyword, per_page=1)
    if results:
        return results[0]
        
    return None


# =============================================================================
#  FUNÇÃO PRINCIPAL (SKILL EXECUTE)
# =============================================================================

def execute(query, say, takeCommand, context=None):
    """Ponto de entrada da skill. Chamado pelo SkillManager."""
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None
    query_lower = query.lower()

    # --- STATUS DAS COTAS DE API ---
    if any(w in query_lower for w in ["cota", "limite", "requisições", "quota", "api status", "uso das apis"]):
        try:
            from core.rate_limiter import get_status, print_status
            print_status()
            status = get_status()
            linhas = []
            for api, info in status.items():
                linhas.append(f"{api.capitalize()}: {info['hourly']} nesta hora e {info['daily']} hoje")
            say("Aqui está o status atual de uso das nossas APIs: " + ". ".join(linhas) + ".")
        except Exception as e:
            say(f"Não consegui obter o status das cotas: {e}")
        return True

    # --- GERAR PALETA DE CORES ---

    if any(w in query_lower for w in ["paleta", "cores", "esquema de cor", "colormind"]):
        say("Gerando uma paleta de cores harmônica para você...")

        # Tenta extrair uma cor base da query
        seed = None
        hex_match = re.search(r'#([0-9a-fA-F]{6})', query)
        if hex_match:
            hex_val = hex_match.group(1)
            seed = [int(hex_val[i:i+2], 16) for i in (0, 2, 4)]

        palette = generate_color_palette(seed)
        if palette:
            colors_str = " | ".join(palette)
            print(f"\n🎨 PALETA GERADA: {colors_str}\n")
            say(f"Paleta gerada com sucesso: {colors_str}. Você pode usar essas cores no seu próximo projeto.")
        else:
            say("Não consegui gerar a paleta. O serviço pode estar temporariamente fora do ar.")
        return True

    # --- BUSCAR VÍDEO B-ROLL ---
    if any(w in query_lower for w in ["vídeo de fundo", "b-roll", "vídeo para", "video stock"]):
        topic = re.sub(r'laura|buscar|encontrar|vídeo|de fundo|b-roll|para|stock|video', '', query_lower).strip()
        if not topic:
            say("Qual é o tema do vídeo que você precisa?")
            topic = takeCommand()
            if not topic or topic == "none":
                return True

        say(f"Procurando vídeos B-roll sobre '{topic}'...")
        videos = search_pexels_videos(topic, per_page=3)

        if not videos:
            say("Não encontrei vídeos sobre esse tema. Tente outro termo de busca.")
            return True

        say(f"Encontrei {len(videos)} vídeos profissionais gratuitos:")
        for i, v in enumerate(videos, 1):
            say(f"Vídeo {i}: {v['width']}x{v['height']}, duração {v['duration']}s")

        say("Deseja que eu baixe algum deles?")
        resp = takeCommand()
        if resp and any(w in resp.lower() for w in ["sim", "baixe", "todos", "primeiro", "quero"]):
            for i, v in enumerate(videos):
                ext = "mp4"
                filename = f"{topic.replace(' ', '_')}_{i+1}.{ext}"
                filepath = download_asset(v["url"], filename, subfolder="videos")
                if filepath:
                    say(f"Vídeo {i+1} salvo em: {filepath}")
            say("Downloads concluídos.")
        else:
            say("Tudo bem, os links estão disponíveis se precisar.")

        return True

    # --- BUSCAR FOTOS (PADRÃO) ---
    topic = re.sub(r'laura|buscar|encontrar|imagem|foto|profissional|para|de|sobre|stock|unsplash|pexels|banco', '', query_lower).strip()
    if not topic:
        say("Qual é o tema da foto que você precisa? Por exemplo: tecnologia, natureza, escritório...")
        topic = takeCommand()
        if not topic or topic == "none":
            return True

    say(f"Varrendo bancos de imagens profissionais sobre '{topic}'...")

    # Busca em ambas as plataformas
    pexels_results = search_pexels_photos(topic, per_page=3)
    unsplash_results = search_unsplash_photos(topic, per_page=3)
    all_results = pexels_results + unsplash_results

    if not all_results:
        say("Não encontrei fotos sobre esse tema. Verifique se as chaves de API estão configuradas no .env.")
        return True

    say(f"Encontrei {len(all_results)} fotos profissionais gratuitas sobre '{topic}':")
    for i, photo in enumerate(all_results, 1):
        source = photo['source'].capitalize()
        photographer = photo.get('photographer', 'Desconhecido')
        say(f"Foto {i}: por {photographer} ({source})")

    say("Deseja que eu baixe essas fotos para a pasta de assets do projeto?")
    resp = takeCommand()
    if resp and any(w in resp.lower() for w in ["sim", "baixe", "todos", "quero", "pode"]):
        for i, photo in enumerate(all_results):
            ext = "jpg"
            filename = f"{topic.replace(' ', '_')}_{photo['source']}_{i+1}.{ext}"
            filepath = download_asset(photo["url_large"], filename, subfolder="photos")
            if filepath:
                say(f"Foto {i+1} salva.")
        say("Todas as fotos foram baixadas para a pasta assets_baixados do projeto.")
    else:
        say("Entendido, as fotos estão disponíveis quando precisar.")

    return True
