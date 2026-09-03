import os
import json
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALENDAR_DIR = os.path.join(BASE_DIR, "Calendario_de_Postagens")

DIAS_DA_SEMANA = [
    "1_Segunda-feira",
    "2_Terca-feira",
    "3_Quarta-feira",
    "4_Quinta-feira",
    "5_Sexta-feira",
    "6_Sabado",
    "7_Domingo"
]

SLOTS_DIARIOS = [
    "Post_1_Manha",
    "Post_2_Tarde",
    "Post_3_Noite"
]

def load_channels():
    config_path = os.path.join(BASE_DIR, "config", "quality_guidelines.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("canais", {})
    except Exception as e:
        print(f"[CalendarManager] Erro ao carregar canais: {e}")
        return {}

def build_calendar_tree():
    """Constrói a árvore de diretórios do calendário para os canais ativos."""
    channels = load_channels()
    if not channels:
        print("[CalendarManager] Nenhum canal configurado para criar a árvore.")
        return
        
    os.makedirs(CALENDAR_DIR, exist_ok=True)
    
    for ch_id, ch_data in channels.items():
        ch_dir = os.path.join(CALENDAR_DIR, ch_id)
        os.makedirs(ch_dir, exist_ok=True)
        
        for dia in DIAS_DA_SEMANA:
            dia_dir = os.path.join(ch_dir, dia)
            os.makedirs(dia_dir, exist_ok=True)
            
            for slot in SLOTS_DIARIOS:
                slot_dir = os.path.join(dia_dir, slot)
                os.makedirs(slot_dir, exist_ok=True)
                
    print("[CalendarManager] Árvore de calendário verificada e construída com sucesso.")

def allocate_file(source_filepath, channel_id, dia_semana, slot):
    """
    Move um arquivo (vídeo, áudio ou thumbnail) para a pasta exata do calendário.
    dia_semana deve corresponder ao prefixo numérico ou ao nome exato (ex: '1_Segunda-feira').
    """
    if not os.path.exists(source_filepath):
        print(f"[CalendarManager] Arquivo original não encontrado: {source_filepath}")
        return False
        
    # Match fuzzy para dia da semana e slot (para facilitar uso)
    dia_match = next((d for d in DIAS_DA_SEMANA if dia_semana.lower() in d.lower()), None)
    slot_match = next((s for s in SLOTS_DIARIOS if slot.lower() in s.lower()), None)
    
    if not dia_match or not slot_match:
        print(f"[CalendarManager] Dia ou Slot inválido. Recebido: {dia_semana}, {slot}")
        return False
        
    target_dir = os.path.join(CALENDAR_DIR, channel_id, dia_match, slot_match)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = os.path.basename(source_filepath)
    target_filepath = os.path.join(target_dir, filename)
    
    try:
        shutil.copy2(source_filepath, target_filepath)
        print(f"[CalendarManager] Sucesso: {filename} alocado em {channel_id} > {dia_match} > {slot_match}")
        return target_filepath
    except Exception as e:
        print(f"[CalendarManager] Erro ao alocar arquivo: {e}")
        return False

if __name__ == "__main__":
    # Teste de Inicialização Direta
    build_calendar_tree()
