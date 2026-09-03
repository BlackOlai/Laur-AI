import requests
import json

# Tenta importar yfinance, se não tiver, avisa o usuário depois
try:
    import yfinance as yf
except ImportError:
    yf = None

KEYWORDS = [
    "dólar", "euro", "bitcoin", "cotação", "valor da ação", 
    "quanto está a ação", "bolsa de valores", "preço de",
    "fundo imobiliário", "quanto tá o dólar", "valor do euro"
]

def get_currency_data():
    """Busca cotações de moedas na AwesomeAPI (Grátis e sem chave)."""
    try:
        url = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,BTC-BRL"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro AwesomeAPI: {e}")
    return None

def identify_ticker(query, context):
    """Usa a IA para converter o nome de uma empresa em um ticker da B3."""
    client = context.get("client")
    model = context.get("model_to_use")

    if not client: return None

    prompt = f"""
    Sua tarefa é identificar a empresa, fundo imobiliário ou ativo financeiro mencionado e retornar seu código (ticker) na Bolsa Brasileira (B3).
    Frase do usuário: "{query}"
    
    Regras:
    1. Responda APENAS o código com o sufixo '.SA'. Exemplo: 'PETR4.SA', 'VALE3.SA', 'HGLG11.SA', 'ITUB4.SA'.
    2. Se o usuário já falou o código (ex: "petr4"), apenas garanta que termine com '.SA'.
    3. Se não identificar nenhuma empresa ou fundo, responda 'NONE'.
    4. Não adicione pontuação, aspas ou explicações.
    
    Exemplo: "quanto tá a vale?" -> "VALE3.SA"
    Exemplo: "preço da petrobras" -> "PETR4.SA"
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=15
        )
        ticker = response.choices[0].message.content.strip().upper()
        # Limpeza extra
        ticker = ticker.replace('"', '').replace("'", "").replace(" ", "")
        return ticker if ticker != "NONE" else None
    except:
        return None

def execute(query, say, takeCommand, context=None):
    query = query.lower()
    
    # 1. Caso Moedas (Dólar, Euro, Bitcoin)
    if any(m in query for m in ["dólar", "euro", "bitcoin"]):
        data = get_currency_data()
        if data:
            if "dólar" in query and "USDBRL" in data:
                val = float(data["USDBRL"]["bid"])
                say(f"Senhor, o dólar está cotado em {val:.2f} reais.")
                return True
            elif "euro" in query and "EURBRL" in data:
                val = float(data["EURBRL"]["bid"])
                say(f"O euro está custando {val:.2f} reais no momento.")
                return True
            elif "bitcoin" in query and "BTCBRL" in data:
                val = float(data["BTCBRL"]["bid"])
                say(f"O Bitcoin está em aproximadamente {val:,.0f} reais.")
                return True
        else:
            say("Desculpe senhor, não consegui acessar os dados de câmbio agora.")
            return True

    # 2. Caso Ações/FIIs/Bolsa
    ticker = identify_ticker(query, context)
    if ticker:
        if yf is None:
            say("Senhor, notei que a biblioteca 'yfinance' não está instalada no ambiente. Não consigo verificar ações sem ela.")
            print("[ALERTA] Instale a biblioteca: pip install yfinance")
            return True
            
        say(f"Consultando a cotação de {ticker.replace('.SA', '')} na B3...")
        try:
            stock = yf.Ticker(ticker)
            # Pega o histórico do último dia
            hist = stock.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                say(f"A ação {ticker.replace('.SA', '')} está sendo negociada a {price:.2f} reais.")
            else:
                say(f"Não encontrei dados recentes para o papel {ticker}. Verifique se o código está correto.")
        except Exception as e:
            print(f"Erro yfinance: {e}")
            say(f"Houve uma falha técnica ao buscar a cotação de {ticker}.")
        return True

    # Caso genérico de "cotação" sem alvo claro
    if any(k in query for k in ["cotação", "bolsa de valores", "preço de"]):
        say("Qual moeda ou ação o senhor deseja que eu verifique?")
        resp = takeCommand().lower()
        if resp != "none" and resp != "":
            return execute(resp, say, takeCommand, context)
        return True

    return False
