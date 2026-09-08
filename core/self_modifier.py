"""Self-modification auditada da Laura (Fase 5).

Inspirado no módulo `self-mod/` do Conway-Research/automaton.
Permite que a Laura crie as próprias skills de forma SEGURA:

1. Recebe o código Python de uma skill proposta (gerado pela IA)
2. Valida sintaxe (py_compile) e quality gates (Ruff, se disponível)
3. Valida contra a Constituição (a skill não pode violar leis)
4. Aplica rate limits (máx. N auto-modificações por dia)
5. Registra tudo no audit log (selfmod_log.json)
6. Só então instala em skills/ e sinaliza recarga

Nada é instalado sem passar por TODAS as etapas. Se qualquer validação
falha, o código NUNCA chega à pasta de skills.

Uso:
    from core.self_modifier import propose_skill
    ok, msg = propose_skill(codigo_python, nome="minha_skill", say=say)
"""

import os
import re
import json
import datetime
import py_compile
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
LOG_FILE = os.path.join(BASE_DIR, "selfmod_log.json")

# Rate limits (Lei VII da Constituição — aplicada à auto-evolução)
MAX_PER_DAY = int(os.getenv("MAX_SELFMOD_PER_DAY", "3"))
MAX_LINES = int(os.getenv("MAX_SELFMOD_LINES", "400"))

# Bloqueios de segurança — a skill auto-criada NUNCA pode (Leis I/IV/VI):
DANGEROUS_PATTERNS = [
    (r'\bshutil\.rmtree\b', "LEI IV: deleção recursiva de diretórios"),
    (r'\bos\.rmdir\b', "LEI IV: remoção de diretórios"),
    (r'\bdel\s+\w+\s*/[sS]\b', "LEI IV: comando de deleção do Windows"),
    (r'\bformat\s+\w:', "LEI IV: formatação de disco"),
    (r'\b(subprocess|os\.system).*(reg |regedit|bcdedit|diskpart)', "LEI IV: comando de sistema destrutivo"),
    (r'["\'](?:sk-|gsk_|AIza|ghp_|gho_)[A-Za-z0-9]{10,}', "LEI VI: chave de API hardcoded"),
    (r'\brequests\.(post|put)\b.*credentials', "LEI VI: envio de credenciais"),
    (r'\bopen\s*\(\s*["\'].*credentials', "LEI VI: acesso à pasta de credenciais"),
]

SKILL_HEADER = '''"""Skill auto-gerada pela Laura (self-modification auditada).

Gerada em: {timestamp}
Origem: {origin}
Aprovação: {approval_status}
"""
'''


def _log_event(event, detail=""):
    """Audit log — Lei V: toda auto-modificação fica registrada."""
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
    except Exception:
        logs = []
    logs.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "detail": str(detail)[:300],
    })
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs[-200:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SelfMod] Erro no audit log: {e}")


def _check_rate_limit():
    """Lei VII: máximo de auto-modificações por dia."""
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        today = datetime.date.today().isoformat()
        installed_today = sum(
            1 for l in logs
            if l.get("event") == "installed" and str(l.get("timestamp", "")).startswith(today)
        )
        return installed_today < MAX_PER_DAY, installed_today
    except Exception:
        return True, 0


def _validate_syntax(code, name):
    """Etapa 1: o código precisa compilar."""
    tmp = os.path.join(tempfile.gettempdir(), f"selfmod_{name}.py")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
        py_compile.compile(tmp, doraise=True)
        return True, "OK"
    except py_compile.PyCompileError as e:
        return False, f"Erro de sintaxe: {e}"
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _validate_structure(code):
    """Etapa 2: precisa ter a interface de skill (KEYWORDS + execute)."""
    has_keywords = re.search(r'^KEYWORDS\s*=\s*\[', code, re.MULTILINE)
    has_execute = re.search(r'^def\s+execute\s*\(', code, re.MULTILINE)
    if not has_keywords:
        return False, "Skill sem KEYWORDS — não será carregada pelo SkillManager."
    if not has_execute:
        return False, "Skill sem def execute() — interface obrigatória."
    return True, "OK"


def _validate_safety(code):
    """Etapa 3: Lei IV/VI — padrões perigosos proibidos."""
    for pattern, motivo in DANGEROUS_PATTERNS:
        if re.search(pattern, code):
            return False, f"Código contém padrão proibido ({motivo})."
    return True, "OK"


def _validate_quality_gates(code, name):
    """Etapa 4: quality gates Ruff (se disponível) + tamanho."""
    if code.count("\n") > MAX_LINES:
        return False, f"Skill com {code.count(chr(10))} linhas excede o teto ({MAX_LINES})."
    try:
        import subprocess
        tmp = os.path.join(tempfile.gettempdir(), f"selfmod_{name}.py")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
        result = subprocess.run(
            ["ruff", "check", "--select", "E722,F821", tmp],
            capture_output=True, text=True, timeout=30
        )
        os.remove(tmp)
        if result.returncode != 0:
            return False, f"Quality gate falhou: {result.stdout[:200]}"
        return True, "OK"
    except FileNotFoundError:
        return True, "OK (Ruff não instalado — gates parciais)"
    except Exception as e:
        return True, f"OK (Ruff indisponível: {e})"


def _validate_constitution(code, name):
    """Etapa 5: a skill proposta não pode violar a Constituição.

    Para skills auto-criadas, além do nome, escaneamos o CÓDIGO: se ele
    contém padrões de gasto, publicação pública ou acesso a credenciais,
    é bloqueado — skill auto-criada com potencial de ação irreversível
    exige revisão humana (instalação manual).
    """
    from core.constitution import validate_action
    ok, motivo = validate_action(name, {"self_created": True})
    if not ok:
        return False, f"Constituição: {motivo}"

    # Scan de conteúdo (nomes novos não estão nas listas da constituição)
    code_lower = code.lower()
    spend_patterns = ["daily_budget", "budget", "spend", "adset", "ad_account",
                      "campaign_id", "meta/api/", "graph.facebook.com",
                      "googleads", "billing"]
    publish_patterns = ["graph.instagram.com", "api.twitter.com", "publish",
                        "post_to_feed", "upload_video_youtube", "wordpress_post"]
    for p in spend_patterns:
        if p in code_lower:
            return False, (f"LEI I (scan de código): skill auto-criada contém "
                           f"'{p}' (potencial de gasto real). Instale manualmente "
                           f"após revisão, senhor.")
    for p in publish_patterns:
        if p in code_lower:
            return False, (f"LEI II (scan de código): skill auto-criada contém "
                           f"'{p}' (potencial de publicação pública). Instale "
                           f"manualmente após revisão, senhor.")
    return True, "OK"


def propose_skill(code, name=None, origin="autonomous_agent", say=None):
    """Pipeline completa de auto-modificação auditada.

    Retorna (ok: bool, mensagem: str). Se ok, a skill está instalada em
    skills/ e pronta para ser recarregada ("Laura, recarregar habilidades").
    """
    # Deriva o nome do arquivo do código, se não fornecido
    if not name:
        m = re.search(r'def\s+execute', code)
        name_match = re.search(r'^"""[^\n]*?(\w+)', code)
        name = name_match.group(1) if name_match else "auto_skill"
    name = re.sub(r'[^a-z0-9_]', '', name.lower()) or "auto_skill"

    print(f"[SelfMod] Proposta recebida: {name} ({code.count(chr(10))} linhas, origem={origin})")
    _log_event("proposed", f"{name} via {origin}")

    # Rate limit (Lei VII)
    allowed, count = _check_rate_limit()
    if not allowed:
        msg = (f"Limite diário de auto-modificações atingido ({count}/{MAX_PER_DAY}). "
               "Tente amanhã ou aumente MAX_SELFMOD_PER_DAY no .env.")
        _log_event("blocked_rate_limit", name)
        return False, msg

    # Pipeline de validação — qualquer falha ABORTA a instalação
    checks = [
        ("sintaxe", lambda: _validate_syntax(code, name)),
        ("estrutura", lambda: _validate_structure(code)),
        ("segurança", lambda: _validate_safety(code)),
        ("quality_gates", lambda: _validate_quality_gates(code, name)),
        ("constituição", lambda: _validate_constitution(code, name)),
    ]
    for step_name, check in checks:
        ok, detail = check()
        if not ok:
            msg = f"Falha no gate '{step_name}': {detail}"
            print(f"[SelfMod] {msg}")
            _log_event("rejected", f"{name} — {msg}")
            return False, msg
        print(f"[SelfMod] Gate '{step_name}': OK")

    # Instalação
    skill_path = os.path.join(SKILLS_DIR, f"{name}.py")
    if os.path.exists(skill_path):
        return False, (f"Skill '{name}' já existe. Auto-modificação não "
                       f"sobrescreve código existente (Lei IV).")
    try:
        header = SKILL_HEADER.format(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            origin=origin,
            approval_status=f"auto-aprovada ({MAX_PER_DAY}/dia)"
        )
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(header + code)
    except Exception as e:
        _log_event("install_error", f"{name} — {e}")
        return False, f"Erro ao gravar skill: {e}"

    _log_event("installed", f"{name} ({origin})")
    msg = (f"Skill '{name}' criada e instalada com sucesso. "
           "Diga 'recarregar habilidades' para ativá-la.")
    print(f"[SelfMod] {msg}")
    if say:
        say(msg)
    return True, msg


def get_selfmod_history(n=10):
    """Retorna os últimos N eventos de auto-modificação (para auditoria)."""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)[-n:]
    except Exception:
        pass
    return []

