"""
Skill Protocol da Laura (Fase 2.5) — inspirado no skills/registry do Automaton.

Contrato: toda skill PODE retornar um dict estruturado ao invés de apenas True:

    {
        "status": "ok" | "failed",
        "data": {...},            # dados reais consumíveis pela próxima etapa
        "artifacts": [paths],     # arquivos produzidos
        "summary": "texto curto"  # resumo para relatórios
    }

Retrocompatibilidade: retornos True/False/None ainda são aceitos e
normalizados para o formato acima. Skills antigas não quebram.
"""

import json

def ok(data=None, artifacts=None, summary=""):
    """Retorno padronizado de sucesso."""
    return {
        "status": "ok",
        "data": data or {},
        "artifacts": artifacts or [],
        "summary": summary,
    }

def fail(error="", data=None):
    """Retorno padronizado de falha."""
    return {
        "status": "failed",
        "data": data or {},
        "artifacts": [],
        "summary": str(error),
    }

def normalize(result, skill_name=""):
    """
    Normaliza qualquer retorno de skill para o protocolo.
    True  -> ok (skill legada que só falou)
    False/None -> failed
    dict  -> garantido no formato do protocolo
    """
    if isinstance(result, dict):
        out = {
            "status": result.get("status", "ok"),
            "data": result.get("data", {}),
            "artifacts": result.get("artifacts", []),
            "summary": result.get("summary", ""),
        }
        # Skills antigas podem retornar dicts arbitrários — embala em data
        if "status" not in result:
            out["data"] = result
            out["status"] = "ok"
        return out
    if result is False or result is None:
        return fail(f"{skill_name}: retornou {result}")
    return ok(summary=f"{skill_name}: concluído")

def inject_context(cmd, prev_results, max_chars=1500):
    """
    Injeta o contexto real dos passos anteriores no comando da próxima skill.
    É isso que costura a pipeline: o passo 2 recebe a saída REAL do passo 1.
    """
    if not prev_results:
        return cmd
    ctx_parts = []
    for r in prev_results[-2:]:  # últimos 2 passos bastam
        data_str = json.dumps(r.get("data", {}), ensure_ascii=False)
        if len(data_str) > max_chars:
            data_str = data_str[:max_chars] + "..."
        summary = r.get("summary") or ""
        ctx_parts.append(f"[{r.get('skill', '?')}] {summary}\nDados: {data_str}")
    return f"{cmd}\n\n--- CONTEXTO REAL DOS PASSOS ANTERIORES ---\n" + "\n".join(ctx_parts)
