import os
import sys
import json
import requests
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

KEYWORDS = [
    "buscar versículo", "passagem bíblica", "ler a bíblia", "citação bíblica",
    "história bíblica", "versículo de"
]

def get_bible_verse(reference, translation="almeida"):
    """
    Busca um versículo específico usando a bible-api.com.
    Não requer API Key!
    Exemplo de reference: 'John 3:16' ou 'Genesis 1:1'
    """
    # Mapeamento basico de livros do Português para o Inglês, já que a API prefere o livro em inglês
    # A API bible-api.com aceita a tradução "almeida" para retornar o texto em português.
    book_map = {
        "joão": "John", "joao": "John",
        "gênesis": "Genesis", "genesis": "Genesis",
        "salmos": "Psalms", "salmo": "Psalms",
        "provérbios": "Proverbs", "proverbios": "Proverbs",
        "mateus": "Matthew",
        "marcos": "Mark",
        "lucas": "Luke",
        "romanos": "Romans",
        "apocalipse": "Revelation"
    }
    
    # Substituir nome do livro se estiver no mapa
    ref_lower = reference.lower()
    for pt, en in book_map.items():
        if ref_lower.startswith(pt):
            reference = ref_lower.replace(pt, en, 1)
            break

    url = f"https://bible-api.com/{reference}"
    params = {"translation": translation}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "reference": data.get("reference"),
            "text": data.get("text", "").strip(),
            "translation": data.get("translation_name")
        }
    except Exception as e:
        print(f"[BibleReference] Erro ao buscar versículo '{reference}': {e}")
        return None


def execute(query, say, takeCommand, context=None):
    """Interface de voz da Laura para a skill."""
    query_lower = query.lower()
    
    # Extrai o possível versículo da frase
    # Ex: "Laura, buscar versículo João 3:16"
    reference = re.sub(r'laura|buscar|versículo|passagem|bíblica|ler|a|bíblia|citação|história|de', '', query_lower).strip()
    
    if not reference:
        say("Qual passagem da bíblia você gostaria que eu buscasse? Por exemplo, diga: João 3:16.")
        reference = takeCommand()
        if not reference or reference == "none":
            return True
            
    say(f"Buscando a passagem {reference}...")
    
    verse_data = get_bible_verse(reference)
    
    if not verse_data:
        say("Não consegui encontrar essa passagem. Verifique se o livro e o capítulo estão corretos.")
        return True
        
    say(f"Aqui está o que diz em {verse_data['reference']} na tradução {verse_data['translation']}:")
    say(verse_data["text"])
    
    print(f"\n[Bíblia] {verse_data['reference']}")
    print(f"\"{verse_data['text']}\"\n")
    
    return True
