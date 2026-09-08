"""Detector de padrões de evolução da Laura (Fase 5 — automaton-style).

Analisa o que a Laura fez (jobs no SQLite) e o que o usuário pediu
(chat_history) para encontrar OPORTUNIDADES de criar novas skills:

1. Sequências de skills que se repetem em jobs (ex.: "copywriting ->
   carousel_creator" apareceu 3x) — candidata a skill combinada.
2. Pedidos de chat que caem no fallback genérico repetidamente
   (indicam skill faltante para um tema).

As sugestões ficam em evolution_suggestions.json e aparecem no feed
da HUD. O usuário decide: "Laura, criar skill que <sugestão>".
"""

import os
import re
import json
import datetime
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUGGESTIONS_FILE = os.path.join(BASE_DIR, "evolution_suggestions.json")
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")

MAX_SUGGESTIONS = 10
MIN_SEQUENCE_REPEATS = 2   # sequência de skills precisa repetir N vezes
MIN_THEME_REPEATS = 3      # tema de chat precisa repetir N vezes

_STOPWORDS = set(
    "a o e de da do das dos em no na nos nas um uma uns umas para por com que "
    "qual quais quando onde como eu você voce meu minha seu sua isso aquilo "
    "the of to and in for on is it be me my you your this that la el los las "
    "del al estar ser tem ter fazer quero queria preciso pode poderia faz "
    "sobre então ai oh".split()
)


def _load_suggestions():
    try:
        if os.path.exists(SUGGESTIONS_FILE):
            with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_suggestions(suggestions):
    try:
        with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(suggestions[:MAX_SUGGESTIONS], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[PatternDetector] Erro ao salvar sugestões: {e}")


def _detect_job_sequences():
    """Encontra sequências consecutivas de skills repetidas entre jobs."""
    try:
        from core.state import state
        jobs = state.list_jobs(limit=60, status="done")
    except Exception:
        return []

    seq_counter = Counter()
    for job in jobs:
        skills = [s.get("skill", "") for s in job.get("steps", []) if s.get("skill")]
        for n in (2, 3):
            for i in range(len(skills) - n + 1):
                seq = tuple(skills[i:i + n])
                if len(set(seq)) < n:   # ignora repetição da mesma skill
                    continue
                seq_counter[seq] += 1

    suggestions = []
    for seq, count in seq_counter.most_common():
        if count >= MIN_SEQUENCE_REPEATS:
            suggestions.append({
                "kind": "sequence",
                "pattern": " -> ".join(seq),
                "count": count,
                "suggestion": (f"O fluxo '{' -> '.join(seq)}' rodou {count}x em "
                               f"jobs. Uma skill combinada faria isso em um passo só."),
                "detected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
    return suggestions


def _extract_theme(query):
    """Extrai palavras-chave dominantes de uma query (agrupar temas)."""
    words = re.findall(r"[a-záéíóúâêôãõç]{4,}", query.lower())
    meaningful = [w for w in words if w not in _STOPWORDS]
    return tuple(sorted(meaningful[:3])) if meaningful else None


def _detect_chat_gaps():
    """Encontra temas de chat repetidos — indício de skill faltante.

    Contagem por palavra significativa individual: se uma palavra aparece
    em N queries DIFERENTES, é um tema recorrente (mais robusto que
    agrupar por tuplas de palavras, que falha com ordem variável).
    """
    try:
        if not os.path.exists(CHAT_HISTORY_FILE):
            return []
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return []

    queries = [h.get("content", "") for h in history if h.get("role") == "user"]
    word_queries = {}   # palavra -> set de índices de queries distintas
    for idx, q in enumerate(queries):
        for w in set(re.findall(r"[a-záéíóúâêôãõç]{5,}", q.lower())):
            if w in _STOPWORDS:
                continue
            word_queries.setdefault(w, set()).add(idx)

    suggestions = []
    for word, qidxs in sorted(word_queries.items(), key=lambda x: -len(x[1])):
        count = len(qidxs)
        if count < MIN_THEME_REPEATS:
            continue
        sample = queries[min(qidxs)][:80]
        suggestions.append({
            "kind": "chat_gap",
            "pattern": word,
            "count": count,
            "suggestion": (f"Você me perguntou {count}x sobre '{word}' e eu "
                           f"respondi com conversa genérica. Uma skill dedicada "
                           f"seria mais eficiente. Ex.: \"{sample}\""),
            "detected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        if len(suggestions) >= 5:
            break
    return suggestions


def run_detection(push_activity=None):
    """Roda a detecção completa e atualiza evolution_suggestions.json.

    Retorna as sugestões NOVAS (que não existiam antes).
    """
    current = _detect_job_sequences() + _detect_chat_gaps()
    old = {(s.get("kind"), s.get("pattern")) for s in _load_suggestions()}
    now_keys = {(s["kind"], s["pattern"]) for s in current}

    new = [s for s in current if (s["kind"], s["pattern"]) not in old]
    merged = new + [s for s in _load_suggestions()
                    if (s["kind"], s["pattern"]) not in now_keys]
    _save_suggestions(merged)

    if new and push_activity:
        for s in new[:2]:
            push_activity(f"EVOLUÇÃO: {s['suggestion'][:100]}")
    if new:
        print(f"[PatternDetector] {len(new)} nova(s) sugestão(ões) de evolução.")
    return new


def get_suggestions():
    """Lista atual de sugestões (para consulta por skills/orquestrador)."""
    return _load_suggestions()

