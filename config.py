import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Configuration (fallback)
apikey = os.getenv("AZURE_OPENAI_API_KEY", "")
api_base = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://bhanu-mmjcqyw0-eastus2.openai.azure.com/",
)
api_type = "azure"
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
deployment_name = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT",
    "gpt-5.2-bhanu-model",
)

# YouTube Data API Key
youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")

# Weather API Key (Get free key from: https://www.weatherapi.com/)
weather_api_key = os.getenv("WEATHER_API_KEY", "")

news_api_key = os.getenv("NEWS_API_KEY", "")

# --- NOVO ENGINE: GROQ ---
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

# --- NOVO ENGINE: NVIDIA NIM ---
nvidia_api_key = os.getenv("NVIDIA_API_KEY")
nvidia_model_name = os.getenv("NVIDIA_MODEL_NAME", "minimaxai/minimax-m2.7") # Nome completo: minimaxai/minimax-m2.7

# --- ENGINE ANTIGO: OPENROUTER ---
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_api_base = "https://openrouter.ai/api/v1"
openrouter_model_name = os.getenv("OPENROUTER_MODEL_NAME", "openai/gpt-oss-120b:free")

# --- MOSS-TTS: Servidor Local de TTS de Alta Qualidade ---
# URL do endpoint OpenAI-compatível do servidor MOSS-TTS local.
moss_tts_url = os.getenv("MOSS_TTS_URL", "http://localhost:8000/v1/audio/speech")
# Voz/speaker padrão do MOSS-TTS (nome de speaker ou caminho para áudio de referência).
moss_tts_voice = os.getenv("MOSS_TTS_VOICE", "Ryan")
# Timeout (segundos) para cada requisição ao servidor MOSS-TTS.
moss_tts_timeout = int(os.getenv("MOSS_TTS_TIMEOUT", "20"))


def validate_config():
    """Verifica se as chaves essenciais estão presentes e avisa o usuário."""
    if not openrouter_api_key and not groq_api_key and not nvidia_api_key:
        print("\n\033[93m[AVISO] Nenhuma chave de IA (Groq, NVIDIA ou OpenRouter) encontrada no arquivo .env!\033[0m")
        print("\033[93mO Laura não conseguirá responder sem uma chave válida.\033[0m\n")
        return False
    return True

# Executar validação ao importar
validate_config()

# Cricket API Key (cricketdata.org)
cricket_api_key = os.getenv("CRICKET_API_KEY", "")

# Palavra de Autorização para Auto-Programação do Laura
# NUNCA compartilhe este valor. Também pode ser definida via variável de ambiente LAURA_AUTH_CODE.
laura_auth_code = os.getenv("LAURA_AUTH_CODE", "codigo leao alfa")

