"""
core/rate_limiter.py
====================
Rate Limiter centralizado para todas as APIs externas da Laura.
Protege contra banimentos e esgotamento de cotas com:
  - Contagem de requisições por janela de tempo (hora / dia)
  - Cache de resultados para evitar chamadas repetidas
  - Backoff automático quando se aproxima do limite
  - Alertas de cota para o usuário
"""

import time
import json
import os
import hashlib
from collections import defaultdict
from threading import Lock

# ─── CONFIGURAÇÃO DOS LIMITES POR API ────────────────────────────────────────
# Ajuste esses valores se fizer upgrade de plano nas APIs.
API_LIMITS = {
    "pexels": {
        "hourly": 200,
        "daily": 20000,
        "warn_at_pct": 0.80,   # Avisa ao usuário quando atingir 80% da cota
    },
    "unsplash": {
        "hourly": 50,
        "daily": 5000,
        "warn_at_pct": 0.70,   # Mais conservador: avisa em 70%
    },
    "pinterest": {
        "hourly": 100,
        "daily": 1000,
        "warn_at_pct": 0.80,
    },
    "pixabay": {
        "hourly": 500,
        "daily": 5000,
        "warn_at_pct": 0.80,
    },
    "jamendo": {
        "hourly": 200,
        "daily": 2000,
        "warn_at_pct": 0.80,
    },
}

# Cache em memória (persiste enquanto a Laura estiver rodando)
_cache: dict = {}
_cache_ttl_seconds: int = 3600  # Resultados expiram após 1 hora

# Contadores de uso (em memória, reiniciados a cada restart)
_usage: dict = defaultdict(lambda: {
    "hourly_count": 0,
    "daily_count": 0,
    "last_hour_reset": time.time(),
    "last_day_reset": time.time(),
    "warned_hourly": False,
    "warned_daily": False,
})

_lock = Lock()

# Arquivo de persistência para os contadores diários (sobrevive a restarts)
_PERSIST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "rate_limit_state.json"
)


# ─── PERSISTÊNCIA ────────────────────────────────────────────────────────────

def _load_persisted_state():
    """Carrega o estado do dia atual a partir do arquivo JSON."""
    if not os.path.exists(_PERSIST_PATH):
        return
    try:
        with open(_PERSIST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        today = time.strftime("%Y-%m-%d")
        for api, state in data.items():
            if state.get("date") == today:
                _usage[api]["daily_count"] = state.get("daily_count", 0)
                _usage[api]["last_day_reset"] = state.get("last_day_reset", time.time())
    except Exception as e:
        print(f"[RateLimiter] Erro ao carregar estado: {e}")


def _save_persisted_state():
    """Salva os contadores diários em arquivo para sobreviver a restarts."""
    os.makedirs(os.path.dirname(_PERSIST_PATH), exist_ok=True)
    try:
        today = time.strftime("%Y-%m-%d")
        data = {}
        for api, state in _usage.items():
            data[api] = {
                "date": today,
                "daily_count": state["daily_count"],
                "last_day_reset": state["last_day_reset"],
            }
        with open(_PERSIST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[RateLimiter] Erro ao salvar estado: {e}")


# Carrega estado ao importar o módulo
_load_persisted_state()


# ─── CACHE ───────────────────────────────────────────────────────────────────

def _make_cache_key(api: str, params: dict) -> str:
    """Gera uma chave única de cache baseada na API e nos parâmetros da chamada."""
    raw = f"{api}::{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(api: str, params: dict):
    """
    Retorna resultado cacheado se existir e não estiver expirado.
    Retorna None se não houver cache válido.
    """
    key = _make_cache_key(api, params)
    entry = _cache.get(key)
    if entry and (time.time() - entry["timestamp"]) < _cache_ttl_seconds:
        print(f"[RateLimiter] 💾 Cache HIT para '{api}' | params={params}")
        return entry["data"]
    return None


def set_cached(api: str, params: dict, data):
    """Armazena um resultado no cache em memória."""
    key = _make_cache_key(api, params)
    _cache[key] = {
        "data": data,
        "timestamp": time.time()
    }


# ─── RATE LIMITER PRINCIPAL ──────────────────────────────────────────────────

def can_request(api: str, say_callback=None) -> bool:
    """
    Verifica se é seguro fazer uma requisição para a API informada.

    Args:
        api (str): Nome da API ('pexels', 'unsplash', 'pinterest').
        say_callback: Função say() da Laura para emitir alertas por voz.

    Returns:
        True se a requisição pode ser feita, False se a cota foi atingida.
    """
    api = api.lower()
    limits = API_LIMITS.get(api)
    if not limits:
        # API desconhecida — permite por segurança
        return True

    with _lock:
        state = _usage[api]
        now = time.time()

        # ── Reset das janelas de tempo ──────────────────────────────────────
        if now - state["last_hour_reset"] >= 3600:
            state["hourly_count"] = 0
            state["last_hour_reset"] = now
            state["warned_hourly"] = False
            print(f"[RateLimiter] [Janela] Janela horária da '{api}' resetada.")

        if now - state["last_day_reset"] >= 86400:
            state["daily_count"] = 0
            state["last_day_reset"] = now
            state["warned_daily"] = False
            print(f"[RateLimiter] [Janela] Janela diária da '{api}' resetada.")
            _save_persisted_state()

        hourly_limit = limits["hourly"]
        daily_limit  = limits["daily"]
        warn_pct     = limits["warn_at_pct"]

        # ── Alerta de cota (80% atingido) ───────────────────────────────────
        if not state["warned_hourly"] and state["hourly_count"] >= hourly_limit * warn_pct:
            msg = (f"Atenção: já usei {state['hourly_count']} das "
                   f"{hourly_limit} requisições horárias permitidas para o {api.capitalize()}.")
            print(f"[RateLimiter] [Alerta] {msg}")
            if say_callback:
                say_callback(msg)
            state["warned_hourly"] = True

        if not state["warned_daily"] and state["daily_count"] >= daily_limit * warn_pct:
            msg = (f"Atenção: já usei {state['daily_count']} das "
                   f"{daily_limit} requisições diárias permitidas para o {api.capitalize()}.")
            print(f"[RateLimiter] [Alerta] {msg}")
            if say_callback:
                say_callback(msg)
            state["warned_daily"] = True

        # ── Bloqueio por cota ────────────────────────────────────────────────
        if state["hourly_count"] >= hourly_limit:
            secs = 3600 - (now - state["last_hour_reset"])
            msg = (f"Cota horária da API {api.capitalize()} atingida. "
                   f"Vou aguardar {int(secs // 60)} minutos antes de tentar novamente.")
            print(f"[RateLimiter] [Bloqueio] {msg}")
            if say_callback:
                say_callback(msg)
            return False

        if state["daily_count"] >= daily_limit:
            msg = (f"Cota diária da API {api.capitalize()} foi atingida. "
                   "As buscas visuais serão retomadas amanhã.")
            print(f"[RateLimiter] [Bloqueio] {msg}")
            if say_callback:
                say_callback(msg)
            return False

        return True


def register_request(api: str):
    """
    Incrementa os contadores após uma requisição bem-sucedida.
    Deve ser chamado SOMENTE quando a requisição realmente aconteceu.
    """
    api = api.lower()
    if api not in API_LIMITS:
        return

    with _lock:
        _usage[api]["hourly_count"] += 1
        _usage[api]["daily_count"]  += 1

    # Persiste a cada 10 requisições para não sobrecarregar disco
    if _usage[api]["daily_count"] % 10 == 0:
        _save_persisted_state()

    print(f"[RateLimiter] [Status] {api.upper()} - "
          f"hora: {_usage[api]['hourly_count']}/{API_LIMITS[api]['hourly']} | "
          f"dia: {_usage[api]['daily_count']}/{API_LIMITS[api]['daily']}")


def get_status() -> dict:
    """Retorna um resumo legível do uso atual de cada API."""
    status = {}
    for api, limits in API_LIMITS.items():
        state = _usage[api]
        status[api] = {
            "hourly":  f"{state['hourly_count']}/{limits['hourly']}",
            "daily":   f"{state['daily_count']}/{limits['daily']}",
        }
    return status


def print_status():
    """Imprime o status de uso de forma formatada no terminal."""
    print("\n[Status] STATUS DAS COTAS DE API")
    print("-" * 40)
    for api, info in get_status().items():
        print(f"  {api.upper():12s} | Hora: {info['hourly']:12s} | Dia: {info['daily']}")
    print("─" * 40 + "\n")
