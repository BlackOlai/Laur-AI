import os
import json
import subprocess

# Vozes Edge-TTS (online, Microsoft Azure)
VOICES_EDGE = {
    "thalita": "pt-BR-ThalitaMultilingualNeural",
    "antônio": "pt-BR-AntonioNeural",
    "francisca": "pt-BR-FranciscaNeural"
}

KEYWORDS = ["mudar voz", "trocar voz", "alterar voz", "voz masculina", "voz feminina", "voz antônio", "voz online"]

def execute(query, say, takeCommand, context):
    query = query.lower()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROFILE_PATH = os.path.join(BASE_DIR, "profile.json")

    selected_voice_key = None
    selected_voice_name = None

    # Verifica vozes Edge-TTS
    for name, voice_id in VOICES_EDGE.items():
        if name in query:
            selected_voice_key = voice_id
            selected_voice_name = name
            break

    # Palavras-chave genéricas
    if not selected_voice_key:
        if "masculina" in query:
            selected_voice_key = VOICES_EDGE["antônio"]
            selected_voice_name = "Antônio (Edge-TTS)"
        elif "feminina" in query:
            selected_voice_key = VOICES_EDGE["francisca"]
            selected_voice_name = "Francisca (Edge-TTS)"
        else:
            vozes_msg = "Thalita, Antônio e Francisca pelo Edge-TTS"
            say(f"Quais vozes você quer? Tenho {vozes_msg}. Qual você prefere?")
            return True

    # Salva no profile.json
    try:
        profile = {}
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                profile = json.load(f)

        profile["voice"] = selected_voice_key

        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=4)

        say(f"Entendido. Alterando minha voz para {selected_voice_name}. Como estou agora?")
    except Exception as e:
        print(f"Erro ao mudar voz: {e}")
        say("Houve um problema ao salvar a configuração de voz.")

    return True
