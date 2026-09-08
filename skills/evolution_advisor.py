"""Skill: evolution_advisor — Laura sugere as próprias evoluções (Fase 5).

O usuário pergunta "que habilidades você sugere criar?" e a Laura lista
as sugestões detectadas pelo core/pattern_detector (fluxos repetidos em
jobs + temas de chat sem skill dedicada).
"""

KEYWORDS = [
    "que habilidades você sugere", "sugestões de habilidades",
    "sugerir habilidade", "o que você pode aprender", "sugestões de evolução",
    "como você pode evoluir", "habilidades que faltam",
]


def execute(query, say, takeCommand, context=None):
    try:
        from core.pattern_detector import get_suggestions
        suggestions = get_suggestions()
    except Exception:
        suggestions = []

    if not suggestions:
        say("Por enquanto não detectei padrões que mereçam uma habilidade "
            "nova, senhor. Continuo observando os nossos fluxos.")
        return True

    say(f"Detectei {len(suggestions)} oportunidade(s) de evolução, senhor:")
    for i, s in enumerate(suggestions[:3], 1):
        say(f"Sugestão {i}: {s['suggestion']}")
    say("Se quiser, diga: criar skill que segue uma das sugestões, e eu "
        "projeto e valido o código automaticamente.")
    return True
