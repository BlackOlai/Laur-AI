import os
import requests
import json
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv(override=True)

KEYWORDS = [
    "meta ads", "anúncios meta", "campanhas facebook", "anúncios instagram",
    "gestor de tráfego", "analisar anúncios", "escala de anúncios",
    "facebook ads", "instagram ads", "anúncio validado",
    "listar contas", "minhas contas", "gerenciador de anúncios", "tráfego pago"
]

API_VERSION = "v18.0"

def get_appsecret_proof(token, secret):
    """Gera a prova de segredo do app exigida pelo Meta."""
    return hmac.new(
        secret.encode('utf-8'),
        token.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def get_ad_accounts():
    """Lista as contas de anúncios vinculadas ao token."""
    load_dotenv(override=True)
    token = os.getenv("META_ADS_ACCESS_TOKEN", "").strip()
    secret = os.getenv("META_ADS_APP_SECRET", "").strip()
    
    if not token or not secret:
        return [], "Token ou Secret não configurados no .env"

    url = f"https://graph.facebook.com/{API_VERSION}/me/adaccounts"
    proof = get_appsecret_proof(token, secret)
    
    # Log de depuração (aparece no seu terminal)
    print(f"[DEBUG Meta] Usando Token final: {token[:10]}...{token[-5:]}")
    print(f"[DEBUG Meta] Proof gerado: {proof}")

    params = {
        "access_token": token,
        "appsecret_proof": proof,
        "fields": "name,account_id,currency"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "data" in data:
            return data["data"], None
        if "error" in data:
            return [], data["error"].get("message", "Erro desconhecido")
        return [], "Resposta vazia do Facebook"
    except Exception as e:
        return [], str(e)

def get_campaign_insights(account_id):
    """Puxa os dados de performance da conta selecionada."""
    load_dotenv(override=True)
    token = os.getenv("META_ADS_ACCESS_TOKEN", "").strip()
    secret = os.getenv("META_ADS_APP_SECRET", "").strip()
    
    url = f"https://graph.facebook.com/{API_VERSION}/act_{account_id}/insights"
    proof = get_appsecret_proof(token, secret)
    params = {
        "access_token": token,
        "appsecret_proof": proof,
        "date_preset": "last_7d",
        "fields": "campaign_name,impressions,clicks,spend,ctr,cpc,reach",
        "level": "campaign"
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def execute(query, say, takeCommand, context=None):
    client = context.get("client")
    model = context.get("model_to_use")
    
    load_dotenv(override=True)
    token = os.getenv("META_ADS_ACCESS_TOKEN", "").strip()
    
    if not token:
        say("Senhor, não encontrei o token do Meta Ads no arquivo de configuração.")
        return True

    say("Iniciando inteligência de tráfego Meta Ads. Estou acessando suas contas...")
    
    accounts, error_msg = get_ad_accounts()
    
    if not accounts:
        if error_msg:
            print(f"[Meta API Error] {error_msg}")
            say(f"O Facebook retornou um erro: {error_msg}")
        else:
            say("O token é válido, mas não há contas vinculadas a ele. Verifique as permissões no Gerenciador de Negócios.")
        return True

    if len(accounts) > 1:
        say(f"Encontrei {len(accounts)} contas. Qual delas deseja analisar?")
        for i, acc in enumerate(accounts):
            print(f"[{i}] {acc['name']} (ID: {acc['account_id']})")
        
        escolha = takeCommand(timeout=15)
        # Tenta encontrar a conta pelo nome ou número
        selected_acc = None
        for acc in accounts:
            if acc['name'].lower() in escolha.lower():
                selected_acc = acc
                break
        
        if not selected_acc:
            selected_acc = accounts[0] # Padrão para a primeira se não entender
    else:
        selected_acc = accounts[0]

    say(f"Acessando dados da conta: {selected_acc['name']}.")
    
    insights = get_campaign_insights(selected_acc['account_id'])
    
    if "error" in insights:
        say("Houve um erro ao puxar os dados das campanhas.")
        return True

    ads_data = insights.get('data', [])
    
    if not ads_data:
        say("Não encontrei campanhas com impressões ou cliques nos últimos 7 dias. Vou traçar uma estratégia para você começar do zero.")
        prompt = (
            f"Você é a Laura, Gestora de Tráfego Senior.\n"
            f"Você acabou de analisar a conta de anúncios '{selected_acc['name']}' do Meta Ads, mas ela não possui campanhas ativas ou com resultados nos últimos 7 dias.\n\n"
            f"Sua missão agora é aconselhar o usuário de forma estratégica:\n"
            f"1. Sugira um passo a passo para criar a primeira campanha vencedora.\n"
            f"2. Recomende uma distribuição de orçamento inicial.\n"
            f"3. Dê ideias de 2 criativos (vídeo e imagem) que costumam validar rápido.\n"
            f"Responda de forma direta e inspiradora, como uma verdadeira parceira de negócios."
        )
    else:
        say("Dados coletados. Vou processar a estratégia de otimização agora...")
        prompt = (
            f"Você é a Laura, Gestora de Tráfego Senior.\n"
            f"Analise estes dados de anúncios do Meta Ads da conta '{selected_acc['name']}' (últimos 7 dias):\n\n"
            f"{json.dumps(ads_data, indent=2)}\n\n"
            f"Com base nesses dados:\n"
            f"1. Identifique a campanha campeã.\n"
            f"2. Aponte onde há desperdício de verba (CTR baixo ou CPC alto).\n"
            f"3. Sugira uma estratégia de escala ou ajuste de criativo.\n"
            f"4. Proponha um novo ângulo de anúncio validado para modelagem.\n"
            f"Responda de forma direta e estratégica, como uma parceira de negócios."
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        say(response.choices[0].message.content)
        
    except Exception as e:
        say(f"Erro na análise estratégica: {e}")

    return True
