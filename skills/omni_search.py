KEYWORDS = [
    "pesquisa", "buscar", "procurar", "pesquisar na web", "notícias", 
    "ver vídeo", "buscar imagem", "quem é", "o que é", "onde fica",
    "encontrar", "google", "youtube", "notícias de hoje",
    "ouvir música", "tocar música", "música", "colocar música",
    "ouvi", "ouça", "toca"
]

def execute(query, say, takeCommand, context=None):
    from skills.info_services import get_news, get_full_article
    import webbrowser
    import requests
    import re
    query_lower = query.lower()
    
    if any(k in query_lower for k in ["vídeo", "video", "youtube", "música", "musica", "tocar", "ouvir", "ouvi", "ouça", "toca"]):
        term = query.replace("buscar", "").replace("pesquisar", "").replace("vídeo", "").replace("no youtube", "").replace("ouvir", "").replace("tocar", "").replace("música", "").replace("ouvi", "").replace("ouça", "").replace("toca", "").strip()
        if not term:
            say("O que você deseja ouvir?")
            term = takeCommand(timeout=10)
        
        say(f"Localizando '{term}' para dar o play...")
        
        try:
            # Busca o ID do primeiro vídeo via scraping rápido
            search_url = f"https://www.youtube.com/results?search_query={term.replace(' ', '+')}"
            response = requests.get(search_url)
            video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
            
            if video_ids:
                direct_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                webbrowser.open(direct_url)
                say("Tocando agora, senhor.")
            else:
                webbrowser.open(search_url)
                say("Abri a lista de busca para você escolher.")
        except:
            webbrowser.open(f"https://www.youtube.com/results?search_query={term}")
            say("Abrindo resultados no YouTube.")
        return True

    if any(k in query_lower for k in ["imagem", "foto", "print"]):
        term = query.replace("buscar", "").replace("pesquisar", "").replace("imagem", "").strip()
        say(f"Buscando imagens de {term}...")
        webbrowser.open(f"https://www.google.com/search?tbm=isch&q={term}")
        return True

    if any(k in query_lower for k in ["notícia", "noticia", "acontecendo"]):
        say("Buscando as últimas notícias para você...")
        data = get_news()
        if data and data.get('articles'):
            for i, article in enumerate(data['articles'][:3], 1):
                say(f"{i}: {article['title']}")
            return True

    # Pesquisa Geral Google
    term = query.replace("quem é", "").replace("o que é", "").replace("pesquisar", "").replace("buscar", "").strip()
    say(f"Pesquisando '{term}' na web...")
    webbrowser.open(f"https://www.google.com/search?q={term}")
    
    return True
