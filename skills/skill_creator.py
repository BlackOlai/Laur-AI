from skills.auto_programmer_support import (
    apply_pending_skill,
    cancel_pending_skill,
    generate_skill_code,
    has_pending_skill,
    request_authorization,
    save_pending_skill,
    suggest_skill_filename,
    validate_generated_code,
)


KEYWORDS = [
    "criar nova habilidade",
    "gerar skill",
    "criar skill",
    "desenvolver habilidade",
    "nova skill",
    "criar uma habilidade",
    "criar uma nova habilidade",
    "criar uma skill",
    "desenvolver uma habilidade",
    "me ajuda a criar uma skill",
    "quero criar uma skill",
    "quero criar uma habilidade",
    "adicionar nova habilidade",
    "adicionar uma habilidade",
    "programar nova habilidade",
    "criar novo comando",
    "adicionar novo comando",
    "confirmar alteracao",
    "pode aplicar",
    "sim pode aplicar",
    "aplicar skill pendente",
    "confirmar skill",
    "aplicar a skill",
    "instalar skill",
    "pode instalar",
    "sim pode instalar",
    "pode salvar",
    "sim pode salvar",
    "confirmo a alteracao",
    "cancelar alteracao",
    "nao aplicar",
    "cancelar skill pendente",
    "cancelar skill",
    "descartar skill",
    "nao instalar",
    "nao salvar",
    "cancela a alteracao",
]


def _wants_confirmation(query: str) -> bool:
    return any(
        trigger in query
        for trigger in [
            "confirmar alteracao",
            "pode aplicar",
            "sim pode aplicar",
            "aplicar skill pendente",
            "confirmar skill",
            "aplicar a skill",
            "instalar skill",
            "pode instalar",
            "sim pode instalar",
            "pode salvar",
            "sim pode salvar",
            "confirmo a alteracao",
        ]
    )


def _wants_cancel(query: str) -> bool:
    return any(
        trigger in query
        for trigger in [
            "cancelar alteracao",
            "nao aplicar",
            "cancelar skill pendente",
            "cancelar skill",
            "descartar skill",
            "nao instalar",
            "nao salvar",
            "cancela a alteracao",
        ]
    )


def _extract_description_from_query(query: str) -> str:
    prefixes = [
        "criar nova habilidade",
        "gerar skill",
        "criar skill",
        "desenvolver habilidade",
        "nova skill",
        "criar uma habilidade",
        "criar uma nova habilidade",
        "criar uma skill",
        "desenvolver uma habilidade",
        "me ajuda a criar uma skill",
        "quero criar uma skill",
        "quero criar uma habilidade",
        "adicionar nova habilidade",
        "adicionar uma habilidade",
        "programar nova habilidade",
        "criar novo comando",
        "adicionar novo comando",
    ]
    normalized = query.strip().lower()
    for prefix in prefixes:
        if prefix in normalized:
            start = normalized.find(prefix) + len(prefix)
            remainder = normalized[start:].strip(" :,-")
            cleanup_prefixes = [
                "para a laura ",
                "para laura ",
                "para ",
                "que ",
                "pra ",
            ]
            changed = True
            while changed and remainder:
                changed = False
                for cleanup in cleanup_prefixes:
                    if remainder.startswith(cleanup):
                        remainder = remainder[len(cleanup):].strip()
                        changed = True
            if remainder.startswith("para "):
                remainder = remainder[5:].strip()
            if remainder.startswith("que "):
                remainder = remainder[3:].strip()
            if remainder.startswith("para a laura "):
                remainder = remainder[13:].strip()
            if remainder:
                return remainder
    return ""


def execute(query, say, takeCommand, context=None):
    query = (query or "").lower()
    context = context or {}

    if _wants_confirmation(query):
        success, message = apply_pending_skill(context.get("skill_manager"))
        if success:
            say(f"Perfeito. Instalei a nova habilidade {message} e ja recarreguei minhas skills.")
        else:
            say(message)
        return True

    if _wants_cancel(query):
        _, message = cancel_pending_skill()
        say(message)
        return True

    if not request_authorization(say, takeCommand):
        return True

    description = _extract_description_from_query(query)
    if not description:
        say("Certo. Me diga qual funcionalidade voce quer que eu aprenda.")
        description = takeCommand()

    if not description or description == "none":
        say("Nao consegui entender a funcionalidade desejada. Vou cancelar esta tentativa por enquanto.")
        return True

    client = context.get("client")
    model = context.get("model_to_use") or context.get("openrouter_model_name")
    if not client or not model:
        say("No momento eu nao consegui acessar meu motor de IA para criar essa habilidade.")
        return True

    say("Entendi. Vou estruturar essa nova habilidade agora. Isso pode levar alguns segundos.")

    try:
        code = generate_skill_code(description, client, model)
    except Exception as exc:
        print(f"[SkillCreator] Erro ao gerar skill: {exc}")
        say("Tive um problema ao gerar o codigo dessa habilidade.")
        return True

    valid, reason = validate_generated_code(code)
    if not valid:
        say(f"Por seguranca, eu bloqueei essa habilidade. Motivo: {reason}")
        return True

    suggested_name = suggest_skill_filename(code)
    save_pending_skill(description, code, suggested_name)

    say(f"Pronto. Gerei a habilidade e deixei tudo pendente com o nome sugerido {suggested_name}.")
    say("Se quiser instalar, diga aplicar a skill ou confirmar alteracao. Se preferir descartar, diga cancelar alteracao ou descartar skill.")

    if has_pending_skill():
        print(f"[SkillCreator] Skill pendente salva: {suggested_name}")

    return True
