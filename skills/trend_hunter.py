import requests
import json
import os
import sys

# Garante que a raiz do projeto está no path para as importações locais
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from skills.info_services import get_news

KEYWORDS = [
    "tendências", "trends", "assuntos virais", "o que está em alta",
    "caçadora de tendências", "pesquise tendências", "ideias virais",
    "trend hunter", "o que está bombando", "trending"
]

def fetch_reddit_trends(subreddit="all"):
    """Busca as tendências do Reddit."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=5"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        trends = []
        for post in data.get('data', {}).get('children', []):
            trends.append(post['data']['title'])
        return trends
    except Exception as e:
        print(f"[TrendHunter] Erro Reddit: {e}")
        return []

def fetch_nasa_apod():
    """Busca a curiosidade espacial do dia na NASA."""
    url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title"),
            "explanation": data.get("explanation")
        }
    except Exception as e:
        print(f"[TrendHunter] Erro NASA: {e}")
        return None

def execute(query, say, takeCommand, context=None):
    client = context.get("client") if context else None
    model = context.get("model_to_use") if context else None

    if not client or not model:
        say("Senhor, meus motores de inteligência não estão ativados.")
        return True

    say("Ativando a caçadora de tendências. Vou varrer a internet atrás do que está bombando hoje...")

    trends_data = {}

    print("[TrendHunter] Coletando tendências do Reddit...")
    reddit_trends = fetch_reddit_trends()
    if reddit_trends:
        trends_data["Reddit (Viral)"] = reddit_trends

    print("[TrendHunter] Coletando tendências da NASA...")
    nasa_data = fetch_nasa_apod()
    if nasa_data:
        trends_data["NASA (Ciência e Curiosidades)"] = f"{nasa_data['title']} - {nasa_data['explanation'][:300]}..."

    print("[TrendHunter] Coletando notícias...")
    try:
        news_data = get_news()
        if news_data:
            news_titles = [n.get("title") for n in news_data if n.get("title")]
            trends_data["Notícias"] = news_titles[:5]
    except Exception as e:
        print(f"[TrendHunter] Erro ao buscar notícias: {e}")

    if not trends_data:
        say("Não consegui encontrar tendências. Os serviços podem estar temporariamente fora do ar.")
        from core.skill_protocol import fail
        return fail("nenhuma fonte de tendências disponível")

    context_str = json.dumps(trends_data, ensure_ascii=False, indent=2)
    prompt = f"""Você é a 'Trend Hunter' da MG Solution, especialista em viralização.
Abaixo estão os dados reais de fontes em alta HOJE na internet:
{context_str}

O usuário pediu o seguinte: '{query}'

Crie 3 IDEIAS MATADORAS de conteúdo para redes sociais (Reels/Carrosséis) baseadas apenas nas tendências acima.
Para cada ideia, seja direto, criativo e empolgante. Dê um título e um breve roteiro.
Evite introduções, vá direto às 3 ideias. Use emojis.
"""

    try:
        print("[TrendHunter] Analisando dados com IA...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é a estrategista viral da MG Solution."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        ideias = response.choices[0].message.content.strip()
        print("\n" + "="*40)
        print("💡 TENDÊNCIAS ENCONTRADAS")
        print("="*40)
        print(ideias)
        print("="*40 + "\n")

        # Protocolo estruturado: as ideias REAIS ficam disponíveis para a pipeline
        from core.skill_protocol import ok
        pipeline_result = ok(
            data={"ideias": ideias, "tendencias": trends_data},
            summary="3 ideias de conteúdo geradas a partir de tendências reais",
        )
        
        say("Pronto, mestre! Compilei três ideias virais incríveis baseadas nas tendências de hoje. Confira os detalhes no painel.")

        # Modo autônomo (heartbeat/orquestrador): sem interação de voz —
        # apenas retorna as ideias para a próxima etapa da pipeline.
        if context and context.get("auto_confirm"):
            return pipeline_result

        say("Deseja que eu pegue alguma dessas ideias e já crie um roteiro ou vídeo explicativo?")
        
        # Pega a resposta do usuário
        if takeCommand:
            resposta = takeCommand().lower()
        else:
            resposta = "não"

        if any(w in resposta for w in ["sim", "quero", "primeira", "segunda", "terceira", "ideia", "claro", "por favor", "faça", "criar"]):
            say("Perfeito! Vou encaminhar sua escolha para a fábrica de vídeos.")
            skill_manager = context.get("skill_manager")
            if skill_manager:
                target_skill = next((s for s in skill_manager.skills if s.__name__ == "video_explicativo"), None)
                if target_skill:
                    nova_query = f"criar vídeo explicativo sobre: {resposta} (baseado nas ideias de tendências recém-geradas)"
                    return target_skill.execute(nova_query, say, takeCommand, context)
                else:
                    say("Módulo de vídeos não encontrado.")
            else:
                say("Erro interno no Skill Manager.")
        else:
            say("Tudo bem. Fico à disposição para quando quiser produzir.")
        return pipeline_result

    except Exception as e:
        say("Houve um erro ao gerar as ideias com a inteligência artificial.")
        print(f"[TrendHunter] Erro de LLM: {e}")

    return True
