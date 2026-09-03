import os
import datetime
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, ".chroma_db")

class MemoryManager:
    def __init__(self):
        # Configura o cliente do ChromaDB para armazenar dados localmente
        self.client = chromadb.PersistentClient(path=DB_PATH)
        
        # O DefaultEmbeddingFunction usa o modelo leve all-MiniLM-L6-v2 nativamente
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="laura_memory",
            embedding_function=self.embedding_fn
        )

    def add_memory(self, text, source="chat", additional_metadata=None):
        """Salva uma nova informação na memória de longo prazo."""
        if not text.strip():
            return False
            
        memory_id = f"mem_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        metadata = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source": source
        }
        if additional_metadata:
            metadata.update(additional_metadata)
            
        try:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[memory_id]
            )
            print(f"[MemoryManager] Memória salva: {text[:30]}...")
            return memory_id
        except Exception as e:
            print(f"[MemoryManager] Erro ao salvar memória: {e}")
            return None

    def search_memory(self, query, k=3):
        """Busca as K memórias mais relevantes baseadas na semântica da query."""
        try:
            # Pular busca se a coleção estiver vazia
            if self.collection.count() == 0:
                return []
                
            # Define K dinamicamente para não ultrapassar o tamanho da coleção
            actual_k = min(k, self.collection.count())
            if actual_k == 0:
                return []
                
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_k
            )
            
            if not results['documents'] or len(results['documents'][0]) == 0:
                return []
                
            memories = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                memories.append({
                    "text": doc,
                    "metadata": meta
                })
            return memories
        except Exception as e:
            print(f"[MemoryManager] Erro ao buscar memória: {e}")
            return []

    def delete_memory(self, memory_id):
        """Deleta uma memória específica pelo ID."""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"[MemoryManager] Erro ao deletar memória: {e}")
            return False
