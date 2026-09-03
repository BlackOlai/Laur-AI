import webbrowser

KEYWORDS = ["abrir", "acessar o site", "navegar para"]

def execute(query, say, takeCommand, context=None):
    query = query.lower()
    
    sites = {
        "youtube": "https://www.youtube.com",
        "wikipedia": "https://www.wikipedia.com",
        "google": "https://www.google.com",
        "amazon": "https://www.amazon.com",
        "linkedin": "https://www.linkedin.com",
        "netflix": "https://www.netflix.com",
        "chat gpt": "https://www.chatgpt.com",
        "github": "https://www.github.com"
    }

    found = False
    for key, url in sites.items():
        if key in query:
            say(f"Abrindo o {key} senhor...")
            webbrowser.open(url)
            found = True
            break
            
    if not found:
        say("Não encontrei esse site na minha lista, senhor. Devo pesquisar no Google?")
        ans = takeCommand().lower()
        if "sim" in ans or "pode" in ans:
            # Extrai o nome do site tentando remover o "abrir"
            search_query = query.replace("abrir", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={search_query}")
