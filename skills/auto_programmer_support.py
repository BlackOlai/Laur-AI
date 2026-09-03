import ast
import datetime
import json
import os
import re

from config import laura_auth_code


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
PENDING_STATE_PATH = os.path.join(BASE_DIR, ".autoprog_pendente.json")

MAX_AUTH_ATTEMPTS = 3

# Heuristica simples de bloqueio para reduzir risco de codigo perigoso.
FORBIDDEN_SNIPPETS = [
    "os.remove",
    "os.rmdir",
    "shutil.rmtree",
    "shutil.move",
    "subprocess.",
    "eval(",
    "exec(",
    "__import__(",
    "open(",
    "Path.unlink",
    "requests.delete",
    "httpx.delete",
    "powershell",
    "cmd.exe",
]

SYSTEM_PROMPT = """Voce gera apenas codigo Python para uma skill do assistente Laura.

Requisitos obrigatorios:
- Retorne apenas o codigo Python, sem explicacoes.
- O arquivo deve conter KEYWORDS e a funcao execute(query, say, takeCommand, context=None).
- A resposta deve ser em portugues do Brasil, sem emojis.
- A skill deve ser humanizada: se precisar de varias informacoes, tente extrai-las da 'query' inicial primeiro usando a IA (client) antes de perguntar ao usuario.
- Ao perguntar, use um tom elegante, cordial e fluido, nunca como um interrogatorio robotico.
- Evite operacoes destrutivas, execucao de shell, remocao de arquivos e modificacao do nucleo.
"""


def verify_authorization(code: str) -> bool:
    if not code:
        return False
    return code.strip().lower() == laura_auth_code.strip().lower()


def request_authorization(say, take_command) -> bool:
    say("Essa funcao e protegida. Por favor, informe o codigo de autorizacao para continuar.")

    for attempt in range(1, MAX_AUTH_ATTEMPTS + 1):
        provided = take_command()
        if not provided or provided == "none":
            if attempt < MAX_AUTH_ATTEMPTS:
                say("Nao consegui entender o codigo. Tente novamente.")
            continue

        if verify_authorization(provided):
            say("Codigo confirmado. Acesso liberado.")
            return True

        remaining = MAX_AUTH_ATTEMPTS - attempt
        if remaining > 0:
            say(f"Codigo incorreto. Restam {remaining} tentativas.")

    say("Voce excedeu o limite de tentativas. Vou manter essa operacao bloqueada.")
    return False


def build_generation_prompt(description: str) -> str:
    return f"""Crie uma skill completa para a Laura com base na descricao abaixo.

Descricao:
{description}

Diretrizes de Implementacao:
1. Extracao de Dados: Se a funcionalidade exige parametros (ex: nome, data, tipo), o codigo deve primeiro tentar extrair esses dados da 'query' inicial usando o 'client' de IA disponivel no 'context'.
2. Dialogo Humano: Se faltarem dados, use say(...) para pedir de forma natural e takeCommand() para ouvir. Nao faça uma sequencia de perguntas mecanicas.
3. Formato:
import os
import json

KEYWORDS = ["frase 1", "frase 2"]

def execute(query, say, takeCommand, context=None):
    client = context.get("client")
    model = context.get("model_to_use")
    # Logica para extrair dados da query e interagir elegantemente
    ...
    return True

Regras:
- Nao inclua markdown na resposta.
- Retorne APENAS o codigo Python.
"""


def generate_skill_code(description: str, client, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_generation_prompt(description)},
        ],
        temperature=0.2,
        max_tokens=1800,
    )
    code = response.choices[0].message.content or ""
    return strip_code_fences(code)


def strip_code_fences(text: str) -> str:
    return re.sub(r"```(?:python)?|```", "", text).strip()


def validate_generated_code(code: str) -> tuple[bool, str]:
    if not code.strip():
        return False, "Nenhum codigo foi gerado."

    for snippet in FORBIDDEN_SNIPPETS:
        if snippet.lower() in code.lower():
            return False, f"Trecho bloqueado por seguranca: {snippet}"

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Codigo invalido gerado pela IA: linha {exc.lineno}"

    has_keywords = any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "KEYWORDS" for target in node.targets)
        for node in tree.body
    )
    has_execute = any(isinstance(node, ast.FunctionDef) and node.name == "execute" for node in tree.body)

    if not has_keywords:
        return False, "A skill gerada nao possui KEYWORDS."
    if not has_execute:
        return False, "A skill gerada nao possui a funcao execute."

    return True, ""


def suggest_skill_filename(code: str) -> str:
    match = re.search(r"KEYWORDS\s*=\s*\[(.*?)\]", code, re.DOTALL)
    if match:
        raw = match.group(1).split(",")[0].strip().strip('"\'')
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
        if slug:
            return f"skill_{slug}.py"

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"auto_skill_{timestamp}.py"


def save_pending_skill(description: str, code: str, suggested_name: str) -> None:
    payload = {
        "description": description,
        "code": code,
        "suggested_name": suggested_name,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    with open(PENDING_STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def has_pending_skill() -> bool:
    return os.path.exists(PENDING_STATE_PATH)


def load_pending_skill() -> dict | None:
    if not has_pending_skill():
        return None
    with open(PENDING_STATE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def clear_pending_skill() -> None:
    if has_pending_skill():
        os.remove(PENDING_STATE_PATH)


def apply_pending_skill(skill_manager=None) -> tuple[bool, str]:
    payload = load_pending_skill()
    if not payload:
        return False, "Nao encontrei nenhuma habilidade pendente para instalar."

    valid, reason = validate_generated_code(payload.get("code", ""))
    if not valid:
        clear_pending_skill()
        return False, f"Descartei a habilidade pendente por seguranca. Motivo: {reason}"

    os.makedirs(SKILLS_DIR, exist_ok=True)

    filename = ensure_unique_filename(payload.get("suggested_name") or "auto_skill.py")
    file_path = os.path.join(SKILLS_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(payload.get("code", ""))

    clear_pending_skill()

    if skill_manager:
        skill_manager.load_skills()

    return True, filename


def cancel_pending_skill() -> tuple[bool, str]:
    if not has_pending_skill():
        return False, "Nao existe nenhuma habilidade pendente para cancelar."

    clear_pending_skill()
    return True, "Tudo certo. Cancelei a alteracao e nada foi instalado."


def ensure_unique_filename(filename: str) -> str:
    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".py"

    candidate = f"{base}{ext}"
    counter = 1
    while os.path.exists(os.path.join(SKILLS_DIR, candidate)):
        candidate = f"{base}_{counter}{ext}"
        counter += 1
    return candidate
