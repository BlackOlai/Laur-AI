import requests
import json
import os
import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv(override=True)
news_api_key = os.getenv("NEWS_API_KEY", "")
weather_api_key = os.getenv("WEATHER_API_KEY", "")

try:
    import trafilatura
except ImportError:
    trafilatura = None

KEYWORDS = ["previsão do tempo", "clima", "temperatura", "notícias", "notícia", "acontecendo no mundo"]

def extract_city(query, context):
    """Usa a IA para descobrir qual cidade o usuário mencionou."""
    client = context.get("client")
    model = context.get("model_to_use")
    if not client: return "Porto Alegre" # Fallback

    prompt = f"""
    Sua tarefa é extrair o nome da cidade e o estado de uma frase.
    Frase: "{query}"
    Regras: Responda APENAS o nome da cidade e o estado. Se não houver, use Porto Alegre.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except: return "Porto Alegre"

def get_weather_pro(city):
    """WeatherAPI.com (Necessita chave)"""
    if not weather_api_key: return None
    url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city}&lang=pt"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "city": f"{data['location']['name']}, {data['location']['region']}",
                "temp": data['current']['temp_c'],
                "humidity": data['current']['humidity'],
                "condition": data['current']['condition']['text'],
                "wind_kph": data['current']['wind_kph'],
                "source": "WeatherAPI"
            }
    except: return None

def get_weather_open_meteo(city):
    """Fallback gratuito usando Open-Meteo"""
    return {"city": city, "temp": "desconhecida", "humidity": "N/A", "condition": "não disponível", "source": "Open-Meteo"}

def get_cotacao():
    """ Busca cotação do dólar e euro."""
    try:
        url = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "dolar": data.get("USDBRL", {}).get("bid", "N/A"),
                "euro": data.get("EURBRL", {}).get("bid", "N/A"),
                "dolar_formatted": data.get("USDBRL", {}).get("name", "Dólar"),
                "euro_formatted": data.get("EURBRL", {}).get("name", "Euro")
            }
    except:
        return None

def get_news_ia():
    """Busca notícia de IA ou tecnologia."""
    if not news_api_key or "SUA_CHAVE" in news_api_key:
        return None
    url = "https://newsapi.org/v2/everything"
    params = {
        "apiKey": news_api_key,
        "q": "inteligência artificial OR AI OR ChatGPT OR tecnologia",
        "language": "pt",
        "sortBy": "publishedAt",
        "pageSize": 1
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("articles"):
                article = data["articles"][0]
                return {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "")
                }
    except:
        return None

NEWS_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "widget_data.json")

def save_widget_data(data):
    """Salva dados no cache."""
    try:
        with open(NEWS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass

def get_widget_data():
    """Carrega dados do cache."""
    if os.path.exists(NEWS_CACHE_FILE):
        try:
            with open(NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return None

def update_widget_cache(city="Porto Alegre"):
    """Atualiza dados do widget (chamado periodicamente)."""
    weather = get_weather_pro(city) or get_weather_open_meteo(city)
    cotacao = get_cotacao()
    news_ia = get_news_ia()
    
    data = {
        "weather": weather,
        "cotacao": cotacao,
        "news_ia": news_ia,
        "updated": datetime.datetime.now().strftime("%d/%m %H:%M")
    }
    save_widget_data(data)
    return data

def get_news(topic=None, category=None):
    """Busca notícias com filtros aprimorados."""
    if not news_api_key or "SUA_CHAVE" in news_api_key:
        return None
    params = {"apiKey": news_api_key, "pageSize": 5}
    if category and not topic:
        base_url = "https://newsapi.org/v2/top-headlines"
        params["category"] = category
        params["country"] = "br"
    elif topic:
        base_url = "https://newsapi.org/v2/everything"
        params["q"] = topic
        params["searchIn"] = "title"
        params["language"] = "pt"
        params["sortBy"] = "publishedAt"
    else:
        base_url = "https://newsapi.org/v2/top-headlines"
        params["country"] = "br"
    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200: return response.json()
    except: return None

def get_full_article(url):
    """Busca o conteúdo completo de um site usando Jina Reader (prioritário) ou fallbacks."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # MÉTODO 1: Jina Reader (Excelente para sites com JS/Vercel)
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, headers=headers, timeout=15)
        if response.status_code == 200 and len(response.text) > 200:
            print(f"[Scraper] Jina Reader extraiu {len(response.text)} caracteres.")
            return response.text[:15000]
    except Exception as e:
        print(f"[Scraper] Jina Reader falhou: {e}")

    # MÉTODO 2: Trafilatura (Fallback 1)
    if trafilatura:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_comments=False, include_tables=False, no_fallback=False)
                if result and len(result) > 200:
                    return result
        except Exception as e:
            print(f"Trafilatura falhou: {e}")
    
    # MÉTODO 3: BeautifulSoup (Fallback 2)
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            if len(text) > 200:
                return text[:15000]
    except Exception as e:
        print(f"BeautifulSoup falhou: {e}")
    
    return None

def get_youtube_transcript(url):
    """Extrai a transcrição de um vídeo do YouTube."""
    import re
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("Biblioteca youtube_transcript_api não instalada.")
        return None

    # Extrair ID do vídeo
    video_id = None
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/watch" in url:
        match = re.search(r"v=([^&]+)", url)
        if match:
            video_id = match.group(1)
    elif "youtube.com/shorts/" in url:
        video_id = url.split("youtube.com/shorts/")[1].split("?")[0]
            
    if not video_id:
        return None
        
    try:
        # Tentar pegar em português primeiro
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'pt-BR'])
        except:
            # Se falhar, pega qualquer um disponível (geralmente em inglês)
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as e:
                # Se não houver transcrição nenhuma, lança o erro final
                print(f"Vídeo sem legendas ativadas: {e}")
                return None
                
        if data:
            text = " ".join([item['text'] for item in data])
            return text
            
    except Exception as e:
        print(f"Erro ao extrair transcrição do YouTube: {e}")
        return None

def summarize_news(text, context, custom_prompt=None, max_tokens=400):
    """Usa a IA para criar um resumo ou análise amigável para voz."""
    client = context.get("client")
    model = context.get("model_to_use")
    if not client or not text: return None
    
    prompt = custom_prompt if custom_prompt else f"Resuma a seguinte notícia para leitura em voz alta (máx 2 parágrafos):\n\n{text[:6000]}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except: return None

def execute(query, say, takeCommand, context=None):
    query = query.lower()
    
    if any(w in query for w in ["tempo", "clima", "temperatura"]):
        say("Deixe-me verificar o clima...")
        city = extract_city(query, context)
        data = get_weather_pro(city) or get_weather_open_meteo(city)
        say(f"Em {data['city']}, a temperatura é de {data['temp']} graus, umidade de {data['humidity']}%.")

    elif "notícia" in query or "notícias" in query:
        topic = None
        category = None
        if "tecnologia" in query:
            category = "technology"
            say("Buscando notícias de tecnologia...")
        elif "ia" in query or "inteligência artificial" in query:
            topic = '"inteligência artificial" OR "OpenAI" OR "ChatGPT"'
            say("Verificando avanços em IA...")
        else:
            say("Buscando as últimas manchetes...")
            
        data = get_news(topic=topic, category=category)
        if data and data.get('articles'):
            articles = data['articles'][:3]
            for i, article in enumerate(articles, 1):
                title = article['title'].split(" - ")[0]
                say(f"Notícia {i}: {title}")
            
            say("Deseja saber mais detalhes?")
            choice = takeCommand().lower()
            if any(w in choice for w in ["sim", "quero", "pode", "notícia", "primeira", "segunda", "terceira", "1", "2", "3"]):
                index = -1
                if any(w in choice for w in ["primeira", "1", "um"]): index = 0
                elif any(w in choice for w in ["segunda", "2", "dois"]): index = 1
                elif any(w in choice for w in ["terceira", "3", "três", "última"]): index = 2
                
                if index == -1:
                    say("Qual delas? A primeira, segunda ou terceira?")
                    choice = takeCommand().lower()
                    if any(w in choice for w in ["primeira", "1"]): index = 0
                    elif any(w in choice for w in ["segunda", "2"]): index = 1
                    elif any(w in choice for w in ["terceira", "3"]): index = 2

                if index != -1 and index < len(articles):
                    selected = articles[index]
                    detail = selected.get('description', '')
                    url = selected.get('url')
                    say(f"Resumo inicial: {detail}")
                    
                    if url:
                        say("Deseja que eu leia a notícia completa ou apenas abra o site?")
                        answer = takeCommand().lower()
                        if any(w in answer for w in ["leia", "ler", "resumo", "completa"]):
                            say("Analisando o conteúdo original...")
                            full_text = get_full_article(url)
                            summary = summarize_news(full_text, context) if full_text else None
                            if summary:
                                say(summary)
                                say("Deseja que eu abra o site para ver imagens?")
                                ans = takeCommand().lower()
                                if any(w in ans for w in ["sim", "pode", "quero", "abre"]):
                                    import webbrowser
                                    webbrowser.open(url)
                                else:
                                    say("Entendido, senhor. Estarei à disposição para outras buscas.")
                            else:
                                say("Não consegui extrair o texto completo. Vou abrir o site.")
                                import webbrowser
                                webbrowser.open(url)
                        elif any(w in answer for w in ["abre", "abrir", "site"]):
                            import webbrowser
                            webbrowser.open(url)
                    else: say("Deseja mais alguma coisa?")
            else: say("Entendido, senhor.")
    return True
