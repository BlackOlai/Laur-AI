"""
Skill: File Manager (Gerenciador de Arquivos e Pastas)
Inspirada no Code Interpreter do Qwen-Agent, esta skill permite que a Laura
acesse, organize e manipule arquivos e pastas do computador via linguagem natural.

Capacidades:
- Abrir pasta no Explorer
- Listar conteúdo de uma pasta
- Buscar arquivos por nome ou tipo
- Mover / Copiar arquivos
- Deletar arquivos (com confirmação)
- Organizar pasta automaticamente por tipo (PDFs, Imagens, Videos, etc.)
- Criar novas pastas
- Obter informações de um arquivo (tamanho, data)
"""

import os
import shutil
import subprocess
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

KEYWORDS = [
    "abrir pasta", "abrir a pasta", "abrir o explorador", "abrir explorer",
    "listar arquivos", "listar pasta", "listar a pasta", "ver arquivos",
    "ver a pasta", "organizar pasta", "organizar arquivos", "organizar a pasta",
    "mover arquivo", "copiar arquivo", "deletar arquivo", "apagar arquivo",
    "buscar arquivo", "procurar arquivo", "encontrar arquivo", "criar pasta",
    "nova pasta", "gerenciar arquivos", "acessar pasta", "mostrar arquivos",
    "o que tem na pasta", "quais arquivos", "pasta de downloads", "pasta documentos",
    "renomear arquivo"
]

# Pastas conhecidas do Windows
KNOWN_FOLDERS = {
    "downloads": str(Path.home() / "Downloads"),
    "documentos": str(Path.home() / "Documents"),
    "documents": str(Path.home() / "Documents"),
    "desktop": str(Path.home() / "Desktop"),
    "área de trabalho": str(Path.home() / "Desktop"),
    "area de trabalho": str(Path.home() / "Desktop"),
    "imagens": str(Path.home() / "Pictures"),
    "pictures": str(Path.home() / "Pictures"),
    "músicas": str(Path.home() / "Music"),
    "musicas": str(Path.home() / "Music"),
    "videos": str(Path.home() / "Videos"),
    "vídeos": str(Path.home() / "Videos"),
}

# Categorias para organização automática
FILE_CATEGORIES = {
    "📄 Documentos":  [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".md"],
    "🖼️ Imagens":     [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "🎬 Vídeos":      [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "🎵 Áudios":      [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"],
    "📦 Compactados": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "💻 Programas":   [".exe", ".msi", ".bat", ".sh", ".cmd"],
    "📊 Planilhas":   [".xls", ".xlsx", ".csv", ".ods"],
    "🎨 Design":      [".psd", ".ai", ".xd", ".figma", ".sketch"],
    "💾 Código":      [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".sql"],
    "📋 Apresentações": [".ppt", ".pptx", ".key", ".odp"],
}


def _select_folder(title="Selecione uma pasta"):
    """Abre diálogo nativo para escolher pasta."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(title=title)
    root.destroy()
    return folder


def _select_file(title="Selecione um arquivo"):
    """Abre diálogo nativo para escolher arquivo."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file = filedialog.askopenfilename(title=title)
    root.destroy()
    return file


def _detect_folder(query):
    """Detecta se o usuário mencionou uma pasta conhecida na query."""
    query_lower = query.lower()
    for key, path in KNOWN_FOLDERS.items():
        if key in query_lower:
            return path
    return None


def _format_size(size_bytes):
    """Formata tamanho em bytes para leitura humana."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"


def _open_in_explorer(path):
    """Abre uma pasta no Windows Explorer."""
    subprocess.Popen(f'explorer "{path}"')


def _listar_pasta(path, say):
    """Lista o conteúdo de uma pasta de forma organizada."""
    try:
        items = list(os.scandir(path))
        if not items:
            say(f"A pasta está vazia.")
            return

        dirs  = [i for i in items if i.is_dir()]
        files = [i for i in items if i.is_file()]

        resposta = f"Na pasta '{os.path.basename(path)}' encontrei:\n"
        resposta += f"📁 {len(dirs)} pasta(s) e 📄 {len(files)} arquivo(s).\n\n"

        if dirs:
            resposta += "Subpastas:\n"
            for d in sorted(dirs, key=lambda x: x.name)[:10]:
                resposta += f"  📁 {d.name}\n"

        if files:
            resposta += "\nArquivos:\n"
            for f in sorted(files, key=lambda x: x.name)[:15]:
                size = _format_size(f.stat().st_size)
                resposta += f"  📄 {f.name}  ({size})\n"

        if len(files) > 15:
            resposta += f"\n  ... e mais {len(files)-15} arquivo(s)."

        say(resposta)
    except PermissionError:
        say("Não tenho permissão para acessar essa pasta.")


def _organizar_pasta(path, say, takeCommand):
    """Organiza arquivos de uma pasta por categoria/tipo."""
    try:
        items = [f for f in os.scandir(path) if f.is_file()]
        if not items:
            say("Essa pasta não tem arquivos para organizar.")
            return

        # Mapeamento de cada arquivo para sua categoria
        to_move = {}
        for item in items:
            ext = Path(item.name).suffix.lower()
            categoria = "📂 Outros"
            for cat, exts in FILE_CATEGORIES.items():
                if ext in exts:
                    categoria = cat
                    break
            to_move.setdefault(categoria, []).append(item)

        # Preview para o usuário
        preview = f"Vou organizar {len(items)} arquivo(s) em {len(to_move)} pasta(s):\n"
        for cat, files in to_move.items():
            preview += f"  {cat}: {len(files)} arquivo(s)\n"
        preview += "\nPosso prosseguir?"
        say(preview)

        confirmacao = takeCommand(timeout=10)
        if not any(w in (confirmacao or "").lower() for w in ["sim", "pode", "claro", "vai", "ok", "prossiga"]):
            say("Organização cancelada.")
            return

        movidos = 0
        for cat_name, files in to_move.items():
            # Cria nome de pasta limpo (sem emoji para o sistema de arquivos)
            clean_name = cat_name.split(" ", 1)[-1].strip()
            cat_dir = os.path.join(path, clean_name)
            os.makedirs(cat_dir, exist_ok=True)
            for f in files:
                dest = os.path.join(cat_dir, f.name)
                # Evita sobrescrever arquivo com mesmo nome
                if os.path.exists(dest):
                    base, ext = os.path.splitext(f.name)
                    ts = datetime.datetime.now().strftime("%H%M%S")
                    dest = os.path.join(cat_dir, f"{base}_{ts}{ext}")
                shutil.move(f.path, dest)
                movidos += 1

        say(f"Pronto! Organizei {movidos} arquivo(s) com sucesso. Quer que eu abra a pasta para verificar?")
        resp = takeCommand(timeout=10)
        if any(w in (resp or "").lower() for w in ["sim", "pode", "abra", "abrir"]):
            _open_in_explorer(path)

    except Exception as e:
        say(f"Ocorreu um erro durante a organização: {e}")


def _buscar_arquivo(path, term, say):
    """Busca arquivos por nome dentro de uma pasta recursivamente."""
    say(f"Buscando por '{term}' em '{os.path.basename(path)}'...")
    encontrados = []
    try:
        for root, dirs, files in os.walk(path):
            # Ignora pastas ocultas e do sistema
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                if term.lower() in fname.lower():
                    full = os.path.join(root, fname)
                    rel  = os.path.relpath(full, path)
                    size = _format_size(os.path.getsize(full))
                    encontrados.append(f"  📄 {rel}  ({size})")

        if encontrados:
            resultado = f"Encontrei {len(encontrados)} arquivo(s):\n"
            resultado += "\n".join(encontrados[:20])
            if len(encontrados) > 20:
                resultado += f"\n  ... e mais {len(encontrados)-20} resultado(s)."
            say(resultado)
        else:
            say(f"Nenhum arquivo com '{term}' encontrado nessa pasta.")
    except PermissionError:
        say("Permissão negada em parte da pasta.")


def execute(query, say, takeCommand, context=None):
    query_lower = query.lower()

    # ── ABRIR PASTA ──────────────────────────────────────────────────────────
    if any(k in query_lower for k in ["abrir pasta", "abrir a pasta", "abrir explorer", "abrir o explorador", "acessar pasta"]):
        folder = _detect_folder(query)
        if not folder:
            say("Qual pasta você quer que eu abra? Posso abrir Downloads, Documentos, Desktop, Imagens, entre outras — ou selecione manualmente.")
            resp = takeCommand(timeout=10)
            if resp:
                folder = _detect_folder(resp) or _select_folder("Selecione a pasta para abrir")
            else:
                folder = _select_folder("Selecione a pasta para abrir")

        if folder and os.path.exists(folder):
            say(f"Abrindo a pasta '{os.path.basename(folder)}'.")
            _open_in_explorer(folder)
        else:
            say("Não consegui encontrar essa pasta.")
        return True

    # ── LISTAR CONTEÚDO ──────────────────────────────────────────────────────
    if any(k in query_lower for k in ["listar", "ver arquivos", "mostrar arquivos", "o que tem na pasta", "quais arquivos"]):
        folder = _detect_folder(query)
        if not folder:
            say("Em qual pasta você quer que eu liste os arquivos? Posso abrir uma janela para você escolher.")
            resp = takeCommand(timeout=10)
            folder = _detect_folder(resp or "") if resp else None
            if not folder:
                folder = _select_folder("Selecione a pasta para listar")

        if folder and os.path.exists(folder):
            _listar_pasta(folder, say)
        else:
            say("Não encontrei a pasta especificada.")
        return True

    # ── ORGANIZAR PASTA ──────────────────────────────────────────────────────
    if any(k in query_lower for k in ["organizar pasta", "organizar arquivos", "organizar a pasta"]):
        folder = _detect_folder(query)
        if not folder:
            say("Qual pasta você quer organizar? Vou abrir uma janela para selecionar.")
            folder = _select_folder("Selecione a pasta para organizar automaticamente")

        if folder and os.path.exists(folder):
            say(f"Certo. Vou organizar a pasta '{os.path.basename(folder)}' automaticamente por tipo de arquivo.")
            _organizar_pasta(folder, say, takeCommand)
        else:
            say("Não encontrei essa pasta.")
        return True

    # ── BUSCAR ARQUIVO ───────────────────────────────────────────────────────
    if any(k in query_lower for k in ["buscar arquivo", "procurar arquivo", "encontrar arquivo"]):
        say("Qual o nome (ou parte do nome) do arquivo que você está procurando?")
        term = takeCommand(timeout=10)
        if not term:
            say("Não entendi o nome do arquivo.")
            return True

        folder = _detect_folder(query)
        if not folder:
            say("Em qual pasta devo buscar? Posso abrir uma janela para escolher.")
            resp = takeCommand(timeout=10)
            folder = _detect_folder(resp or "") if resp else None
            if not folder:
                folder = _select_folder("Selecione onde buscar o arquivo")

        if folder:
            _buscar_arquivo(folder, term, say)
        return True

    # ── CRIAR PASTA ──────────────────────────────────────────────────────────
    if any(k in query_lower for k in ["criar pasta", "nova pasta"]):
        say("Qual nome você quer dar à nova pasta?")
        nome = takeCommand(timeout=10)
        if not nome:
            say("Não entendi o nome da pasta.")
            return True

        say("Onde devo criar essa pasta? Selecione o local.")
        local = _detect_folder(query) or _select_folder("Selecione onde criar a nova pasta")
        if local:
            nova = os.path.join(local, nome.strip())
            os.makedirs(nova, exist_ok=True)
            say(f"Pasta '{nome}' criada com sucesso em '{os.path.basename(local)}'.")
            _open_in_explorer(nova)
        return True

    # ── MOVER / COPIAR ARQUIVO ───────────────────────────────────────────────
    if any(k in query_lower for k in ["mover arquivo", "copiar arquivo"]):
        acao = "mover" if "mover" in query_lower else "copiar"
        say(f"Selecione o arquivo que você quer {acao}.")
        origem = _select_file(f"Selecione o arquivo para {acao}")
        if not origem:
            say("Operação cancelada.")
            return True

        say(f"Agora selecione a pasta de destino.")
        destino = _select_folder("Selecione a pasta de destino")
        if not destino:
            say("Operação cancelada.")
            return True

        nome_arquivo = os.path.basename(origem)
        dest_path = os.path.join(destino, nome_arquivo)

        if os.path.exists(dest_path):
            say(f"Já existe um arquivo chamado '{nome_arquivo}' no destino. Posso sobrescrever?")
            resp = takeCommand(timeout=10)
            if not any(w in (resp or "").lower() for w in ["sim", "pode", "sobrescreva"]):
                say("Operação cancelada para não sobrescrever.")
                return True

        if acao == "mover":
            shutil.move(origem, dest_path)
        else:
            shutil.copy2(origem, dest_path)

        say(f"Arquivo '{nome_arquivo}' {acao}do com sucesso para '{os.path.basename(destino)}'.")
        return True

    # ── DELETAR ARQUIVO ──────────────────────────────────────────────────────
    if any(k in query_lower for k in ["deletar arquivo", "apagar arquivo"]):
        say("Selecione o arquivo que você quer apagar.")
        arquivo = _select_file("Selecione o arquivo para deletar")
        if not arquivo:
            say("Operação cancelada.")
            return True

        nome = os.path.basename(arquivo)
        say(f"Tem certeza que quer apagar permanentemente o arquivo '{nome}'?")
        resp = takeCommand(timeout=10)
        if any(w in (resp or "").lower() for w in ["sim", "pode", "confirmo", "apague"]):
            os.remove(arquivo)
            say(f"Arquivo '{nome}' apagado com sucesso.")
        else:
            say("Operação cancelada. O arquivo não foi apagado.")
        return True

    # ── RENOMEAR ARQUIVO ─────────────────────────────────────────────────────
    if "renomear arquivo" in query_lower:
        say("Selecione o arquivo que você quer renomear.")
        arquivo = _select_file("Selecione o arquivo para renomear")
        if not arquivo:
            say("Operação cancelada.")
            return True

        nome_atual = os.path.basename(arquivo)
        say(f"O arquivo se chama '{nome_atual}'. Qual deve ser o novo nome?")
        novo_nome = takeCommand(timeout=10)
        if not novo_nome:
            say("Não entendi o novo nome.")
            return True

        # Preserva a extensão original se o usuário não forneceu
        ext_original = Path(arquivo).suffix
        if not Path(novo_nome).suffix:
            novo_nome = novo_nome.strip() + ext_original

        destino = os.path.join(os.path.dirname(arquivo), novo_nome.strip())
        os.rename(arquivo, destino)
        say(f"Arquivo renomeado de '{nome_atual}' para '{novo_nome}' com sucesso.")
        return True

    # ── FALLBACK ─────────────────────────────────────────────────────────────
    say("Posso ajudar com arquivos e pastas. Diga, por exemplo: 'Abrir a pasta de Downloads', 'Listar documentos', 'Organizar a pasta Downloads' ou 'Buscar arquivo'.")
    return True
