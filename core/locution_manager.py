# locution_manager.py — REMOVIDO
# O Coqui XTTS v2 foi descontinuado desta base por ser muito pesado para CPU.
# As locuções de vídeo agora são geradas via:
#   1. Edge TTS (principal)
#   2. Azure Speech TTS (fallback — 500k chars/mês grátis, vozes PT-BR nativas)
#
# Para configurar o Azure TTS, adicione ao .env:
#   AZURE_SPEECH_KEY=sua_chave_aqui
#   AZURE_SPEECH_REGION=eastus
#   AZURE_TTS_VOICE=pt-BR-DonatoNeural  (opcional — padrão: DonatoNeural)

# Stub para não quebrar imports residuais
locution_manager = None
