"""Constituição da Laura — carrega e valida as leis imutáveis.

Inspiração: módulo `constitution.md` do Conway-Research/automaton.
Toda ação autônoma (jobs do heartbeat, orquestração do autonomous_agent)
passa por `validate_action()` ANTES de executar. Se viola uma lei, o job
é bloqueado com o motivo registrado no audit log.

Uso:
    from core.constitution import validate_action
    ok, motivo = validate_action("paid_ads", {"spend": 50.0})
    if not ok:
        say(f"Não posso fazer isso: {motivo}")
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSTITUTION_FILE = os.path.join(BASE_DIR, "constitution.md")

DEFAULTS = {
    "MAX_SPEND_AUTO": 0.0,        # R$ que pode gastar sem aprovação
    "MAX_DELETE_FILES": 3,        # arquivos que pode deletar por job
    "MAX_STEPS_PER_JOB": 8,       # etapas máximas por job
    "MAX_JOBS_PER_HOUR": 6,       # jobs por hora
}


def get_env_num(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def load_constitution_text():
    """Retorna o texto da constituição (para injetar em system prompts)."""
    if not os.path.exists(CONSTITUTION_FILE):
        return ""
    try:
        with open(CONSTITUTION_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[Constitution] Erro ao carregar constitution.md: {e}")
        return ""


def get_rules_summary():
    """Resumo curto das leis para system prompts (economiza tokens)."""
    return (
        "LEIS DA LAURA (Constituição — imutáveis):\n"
        "I. NUNCA gastar dinheiro real sozinha (campanhas: apenas sugerir).\n"
        "II. NUNCA publicar em canais públicos sem passar pelo quality_controller.\n"
        "III. NUNCA mensagens para leads reais sem opt-in + identificação de automação.\n"
        "IV. NUNCA deletar históricos/memórias/DBs; máx 3 arquivos fora do projeto.\n"
        "V. Toda ação autônoma é auditada (SQLite + heartbeat_log + feed HUD).\n"
        "VI. NUNCA enviar credenciais/dados pessoais para serviços externos.\n"
        "VII. Máx 8 etapas por job, máx 6 jobs por hora (aborta com relatório).\n"
        "VIII. Constituição > .env > Olair > decisão autônoma."
    )


# ---------------------------------------------------------------------------
# Validadores por tipo de ação
# ---------------------------------------------------------------------------

# Skills que tocam dinheiro real (Lei I)
SPEND_SKILLS = {
    "paid_ads", "meta_ads_intelligence", "google_ads", "ads_launcher",
    "facebook_ads", "billing", "purchase", "checkout",
}
# Skills que publicam em canais públicos (Lei II)
PUBLISH_SKILLS = {
    "social_media_hub", "youtube_publisher", "instagram_poster",
    "facebook_poster", "linkedin_pro", "twitter_poster", "wordpress_publisher",
}
# Skills que interagem com leads reais (Lei III)
LEAD_SKILLS = {
    "whatsapp_sender", "whatsapp_automation", "email_sender",
    "sales_automator", "crm_outreach",
}
# Skills que deletam coisas (Lei IV)
DELETE_SKILLS = {
    "file_manager", "cleanup", "delete_files", "purge_cache",
}


def validate_action(skill_name, params=None, steps=1):
    """Valida se uma ação autônoma respeita a Constituição.

    Retorna (ok: bool, motivo: str). params: dict opcional com detalhes
    (ex.: {"spend": 50.0}, {"files_to_delete": 5}).
    """
    params = params or {}
    name = (skill_name or "").lower()

    # Lei I — Dinheiro
    if name in SPEND_SKILLS:
        spend = params.get("spend", 0)
        max_spend = get_env_num("MAX_SPEND_AUTO", DEFAULTS["MAX_SPEND_AUTO"])
        if spend and spend > max_spend:
            return False, (
                f"LEI I: gastar R$ {spend} excede o limite autônomo "
                f"(R$ {max_spend}). Sugira a campanha e aguarde aprovação."
            )

    # Lei II — Publicação pública sem quality gate
    if name in PUBLISH_SKILLS:
        if not params.get("quality_approved"):
            return False, (
                "LEI II: publicação pública exige aprovação do "
                "quality_controller antes. Produza e salve localmente; "
                "a publicação fica pendente de revisão."
            )

    # Lei III — Leads reais
    if name in LEAD_SKILLS:
        if not params.get("owner_direct") and not params.get("opt_in"):
            return False, (
                "LEI III: mensagens autônomas para leads reais exigem "
                "opt-in do destinatário e identificação de automação. "
                "Para o próprio Olair, use owner_direct=True."
            )

    # Lei IV — Destruição
    if name in DELETE_SKILLS:
        n_files = params.get("files_to_delete", 1)
        max_del = get_env_num("MAX_DELETE_FILES", DEFAULTS["MAX_DELETE_FILES"])
        if n_files > max_del:
            return False, (
                f"LEI IV: deletar {n_files} arquivos excede o limite "
                f"autônomo ({max_del}). Peça confirmação ao Olair."
            )

    # Lei VII — Rate limits
    max_steps = get_env_num("MAX_STEPS_PER_JOB", DEFAULTS["MAX_STEPS_PER_JOB"])
    if steps > max_steps:
        return False, (
            f"LEI VII: job com {steps} etapas excede o máximo de {max_steps}. "
            "Divida o plano em jobs menores."
        )

    return True, "OK"


def filter_plan(plan_etapas):
    """Valida um plano inteiro do autonomous_agent (lista de etapas).

    Retorna (etapas_permitidas, bloqueios: list[dict]).
    Bloqueia apenas as etapas que violam leis — o resto do job segue.
    """
    permitidas, bloqueios = [], []
    for etapa in plan_etapas:
        skill = etapa.get("skill", "")
        ok, motivo = validate_action(skill, etapa.get("params", {}))
        if ok:
            permitidas.append(etapa)
        else:
            bloqueios.append({"passo": etapa.get("passo"), "skill": skill,
                              "motivo": motivo})
    return permitidas, bloqueios
