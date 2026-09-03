import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_guidelines():
    path = os.path.join(BASE_DIR, "config", "quality_guidelines.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[QualityController] Erro ao carregar guidelines: {e}")
        return {}

def review_json_content(client, model, draft_json, content_type="carrossel ou vídeo"):
    """
    Envia o JSON original gerado pela IA (Escritor) para o Diretor de Criação (Revisor).
    Retorna o JSON aprimorado, mantendo a exata mesma estrutura (chaves e formato).
    """
    guidelines = load_guidelines()
    
    prompt = f"""Você é o Diretor de Criação Implacável (Quality Assurance) da Agência MG Solution.
A sua tarefa é pegar o Rascunho (Draft) abaixo, que foi gerado por um redator júnior para um {content_type}, e REESCREVÊ-LO aplicando estritamente as regras de ouro da nossa agência.

DIRETRIZES DA AGÊNCIA:
{json.dumps(guidelines.get('copywriting', {}), indent=2, ensure_ascii=False)}

RASCUNHO ORIGINAL (DRAFT):
{json.dumps(draft_json, indent=2, ensure_ascii=False)}

O QUE VOCÊ DEVE FAZER:
1. Analisar criticamente cada linha de texto. Se o "Hook" estiver fraco, reescreva-o para ser avassalador. Se o texto estiver professoral, corte e deixe agressivo e magnético.
2. Mantenha EXATAMENTE A MESMA ESTRUTURA JSON que você recebeu (mesmas chaves, mesmos arrays). Apenas altere o CONTEÚDO de texto dentro dos valores.
3. Não adicione nenhuma explicação, comentário ou formatação markdown além do próprio JSON limpo.

Retorne APENAS o JSON aprimorado."""

    print(f"[QualityController] Diretor de Criação revisando o {content_type}...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7 # Um pouco de criatividade para os hooks
        )
        
        # Faz parse da resposta do Revisor
        import re
        raw = response.choices[0].message.content
        cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', raw.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned.strip())
        
        try:
            return json.loads(cleaned)
        except:
            match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            else:
                raise ValueError("JSON não encontrado na resposta do revisor")
    except Exception as e:
        print(f"[QualityController] Erro na revisão: {e}. Retornando o draft original.")
        return draft_json # Fallback seguro: se o revisor falhar, usa o draft original

def review_markdown_content(client, model, draft_md, content_type="e-book"):
    """
    Envia o Markdown original gerado pela IA (Escritor) para o Diretor de Criação.
    """
    guidelines = load_guidelines()
    
    prompt = f"""Você é o Diretor de Criação Implacável (Quality Assurance) da Agência MG Solution.
A sua tarefa é pegar o Rascunho (Draft) abaixo, que foi gerado por um redator júnior para um {content_type}, e REESCREVÊ-LO aplicando estritamente as regras de ouro da nossa agência.

DIRETRIZES DA AGÊNCIA:
{json.dumps(guidelines.get('copywriting', {}), indent=2, ensure_ascii=False)}

RASCUNHO ORIGINAL (DRAFT) EM MARKDOWN:
{draft_md}

O QUE VOCÊ DEVE FAZER:
1. Melhore os títulos para serem ultra persuasivos.
2. Transforme parágrafos longos em frases curtas, dinâmicas e que retenham a leitura.
3. Corte a linguagem robótica.
4. Mantenha a estrutura e a formatação Markdown.

Retorne APENAS o Markdown aprimorado. NADA DE JSON, APENAS MARKDOWN PURO."""

    print(f"[QualityController] Diretor de Criação revisando o {content_type} (Markdown)...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[QualityController] Erro na revisão markdown: {e}. Retornando original.")
        return draft_md
