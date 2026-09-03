import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = None
        if url and key:
            try:
                self.supabase = create_client(url, key)
                print("[DB] Conectado ao Supabase com sucesso.")
            except Exception as e:
                print(f"[DB] Erro ao conectar ao Supabase: {e}")

    def save_analysis(self, table_name: str, data: dict):
        """Salva uma análise genérica no banco de dados."""
        if not self.supabase:
            return False
        try:
            result = self.supabase.table(table_name).insert(data).execute()
            return True
        except Exception as e:
            print(f"[DB] Erro ao salvar na tabela {table_name}: {e}")
            return False

    def get_latest_analysis(self, table_name: str, limit: int = 1):
        """Busca as últimas análises salvas."""
        if not self.supabase:
            return []
        try:
            result = self.supabase.table(table_name).select("*").order("created_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"[DB] Erro ao buscar da tabela {table_name}: {e}")
            return []

    def log_interaction(self, user_query: str, bot_response: str):
        """Registra o histórico de conversa para memória futura."""
        if not self.supabase:
            return
        data = {
            "user_query": user_query,
            "bot_response": bot_response
        }
        self.save_analysis("interactions", data)

# Instância global
db = DatabaseManager()
