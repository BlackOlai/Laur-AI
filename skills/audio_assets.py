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
except ImportError:
    def can_request(api, say_callback=None): return True
    def register_request(api): pass
    def get_cached(api, params): return None
    def set_cached(api, params, data): pass

KEYWORDS = [
    "buscar música", "música de fundo", "trilha sonora", "banco de áudio",
    "jamendo", "música sem direitos", "royalty free music", "audio para video",
    "música motivacional", "música épica", "música triste", "baixar música"
]

ASSETS_DIR = os.path.join(BASE_DIR, "assets_baixados", "audio")
os.makedirs(ASSETS_DIR, exist_ok=True)


def search_jamendo_music(tags, limit=3):
    """
    Busca músicas sem direitos autorais no Jamendo baseado em tags.
    'tags' pode ser uma lista ["epic", "cinematic"] ou string simples "epic".
    A API Jamendo v3 aceita múltiplas tags separadas por espaço na query.
    """
    client_id = os.getenv("JAMENDO_CLIENT_ID", "")
    if not client_id:
        print("[AudioAssets] JAMENDO_CLIENT_ID não configurada no .env")
        return []

    # Normaliza as tags: lista -> string separada por espaço
    if isinstance(tags, list):
        tags_str = " ".join(tags)
    else:
        tags_str = str(tags)

    cache_params = {"tags": tags_str, "limit": limit}

    cached = get_cached("jamendo", cache_params)
    if cached is not None:
        return cached

    if not can_request("jamendo"):
        return []

    url = "https://api.jamendo.com/v3.0/tracks/"
    params = {
        "client_id": client_id,
        "format": "json",
        "limit": limit,
        "fuzzytags": tags_str,
        "include": "musicinfo",
        "audioformat": "mp32",
        "boost": "popularity_total",  # Parâmetro correto da API Jamendo
        # Sem filtro de língua: amplifica o pool de resultados
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        register_request("jamendo")
        data = response.json()
        
        results = []
        for track in data.get("results", []):
            if track.get("audio"):  # Só inclui se tiver URL de áudio válida
                results.append({
                    "id": track["id"],
                    "name": track["name"],
                    "artist": track["artist_name"],
                    "url": track["audio"],
                    "duration": track["duration"],
                    "tags": track.get("musicinfo", {}).get("tags", {}).get("genres", [])
                })
            
        set_cached("jamendo", cache_params, results)
        print(f"[AudioAssets] Jamendo retornou {len(results)} faixas para tags: '{tags_str}'")
        return results
    except Exception as e:
        print(f"[AudioAssets] Erro Jamendo: {e}")
        return []


def download_audio(url, filename):
    """Baixa a trilha sonora MP3."""
    filepath = os.path.join(ASSETS_DIR, filename)
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[AudioAssets] Áudio salvo em: {filepath}")
        return filepath
    except Exception as e:
        print(f"[AudioAssets] Erro no download: {e}")
        return None


# Mapeamento ampliado de moods para tags Jamendo em inglês
# Cada mood tem uma lista de tags para tentar em sequência
MOOD_TAG_MAP = {
    # Conteúdo religioso / espiritual
    "epic cinematic sacred":  ["orchestral", "cinematic", "inspirational", "spiritual", "epic", "ambient"],
    "sacred":                 ["spiritual", "inspirational", "orchestral", "meditative", "ambient"],
    "gospel":                 ["gospel", "inspirational", "spiritual", "uplifting", "choir"],
    "worship":                ["worship", "spiritual", "inspirational", "meditative", "ambient"],
    "inspirational":          ["inspirational", "uplifting", "orchestral", "cinematic", "motivational"],
    # Conteúdo motivacional / negócios
    "motivational epic":      ["motivational", "epic", "powerful", "upbeat", "inspiring"],
    "motivational":           ["motivational", "uplifting", "inspiring", "powerful", "corporate"],
    "epic":                   ["epic", "orchestral", "cinematic", "powerful", "dramatic"],
    # Conteúdo fitness / esporte
    "energetic powerful":     ["energetic", "powerful", "workout", "rock", "intense"],
    "energetic":              ["energetic", "upbeat", "workout", "electronic", "pop"],
    # Genéricos
    "cinematic ambient":      ["cinematic", "ambient", "atmospheric", "orchestral", "piano"],
    "cinematic":              ["cinematic", "orchestral", "atmospheric", "dramatic", "epic"],
    "ambient":                ["ambient", "atmospheric", "meditative", "relaxing", "piano"],
}


def get_best_audio(mood):
    """
    Utilitário para baixar o melhor áudio dado um mood.
    Usa mapeamento de tags expandido e sempre sorteia aleatoriamente
    para garantir variedade entre execuções.
    """
    import random

    # Monta a lista de tags a tentar
    mood_key = mood.strip().lower()
    tag_chain = MOOD_TAG_MAP.get(mood_key, [])

    # Se não achou no mapa, usa o mood diretamente + fallbacks genéricos
    if not tag_chain:
        first_word = mood_key.split()[0] if " " in mood_key else mood_key
        tag_chain = [mood_key, first_word, "cinematic", "ambient", "orchestral", "inspirational"]

    # Remove duplicatas mantendo ordem
    seen = set()
    unique_chain = []
    for t in tag_chain:
        if t and t not in seen:
            seen.add(t)
            unique_chain.append(t)

    for tag in unique_chain:
        print(f"[AudioAssets] Tentando Jamendo com tag: '{tag}'")
        # Busca 50 resultados para pool MAIOR de randomização
        results = search_jamendo_music(tag, limit=50)
        if results:
            import random
            import time
            random.seed(time.time()) # Garante aleatoriedade fresca
            # Sorteia aleatoriamente para não usar sempre a mesma música
            track = random.choice(results)
            filename = f"{tag.split()[0]}_{track['id']}.mp3"
            filepath = download_audio(track['url'], filename)
            if filepath:
                track['local_path'] = filepath
                print(f"[AudioAssets] Trilha sorteada: '{track['name']}' de {track['artist']} (tag: {tag})")
                return track

    print(f"[AudioAssets] Nenhuma trilha encontrada para o mood '{mood}' e seus fallbacks.")
    return None


def execute(query, say, takeCommand, context=None):
    """Interface principal de voz da Laura para a skill."""
    query_lower = query.lower()
    
    say("Estou ativando meu módulo de trilhas sonoras. Qual o clima da música que você procura? Por exemplo: épica, triste, motivacional, relaxante...")
    mood_pt = takeCommand()
    
    if not mood_pt or mood_pt == "none":
        return True
        
    # Mapeamento simples PT -> EN
    mood_map = {
        "épic": "epic",
        "triste": "sad",
        "motivaç": "motivational",
        "inspirad": "inspirational",
        "feliz": "upbeat",
        "relax": "ambient",
        "ambient": "ambient",
        "cinemat": "cinematic",
        "sagr": "spiritual",
        "espiritua": "spiritual",
        "gospel": "gospel",
        "culto": "worship",
        "adoraç": "worship",
        "fé": "inspirational",
        "religios": "spiritual",
        "poderoso": "powerful",
        "energético": "energetic",
        "coral": "orchestral"
    }
    
    mood_en = mood_pt.lower()
    for k, v in mood_map.items():
        if k in mood_en:
            mood_en = v
            break
            
    say(f"Buscando músicas com o clima '{mood_pt}'...")
    tracks = search_jamendo_music(mood_en, limit=3)
    
    if not tracks:
        say("Não encontrei músicas com esse clima, ou a chave do Jamendo não está configurada no .env.")
        return True
        
    say(f"Encontrei {len(tracks)} músicas. Vou listar para você:")
    for i, track in enumerate(tracks, 1):
        say(f"Música {i}: {track['name']}, do artista {track['artist']}. Duração: {track['duration']} segundos.")
        
    say("Deseja que eu baixe alguma delas? Diga 'sim' ou 'baixe todas'.")
    resp = takeCommand()
    if resp and any(w in resp.lower() for w in ["sim", "baixe", "todas"]):
        for track in tracks:
            filename = f"{mood_en}_{track['id']}.mp3"
            filepath = download_audio(track['url'], filename)
            if filepath:
                say(f"{track['name']} salva.")
        say("Downloads concluídos com sucesso.")
    else:
        say("Tudo bem, a busca foi finalizada.")
        
    return True
