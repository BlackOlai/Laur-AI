import os

def replace_in_file(file_path, old_text, new_text):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_text in content or old_text.upper() in content or old_text.lower() in content:
            # Case-sensitive replacements
            new_content = content.replace(old_text, new_text)
            new_content = new_content.replace(old_text.upper(), new_text.upper())
            new_content = new_content.replace(old_text.lower(), new_text.lower())
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Atualizado: {file_path}")
    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

def main():
    base_dir = r"c:\Users\User\Downloads\Laura-A.I-main\Laura-A.I-main"
    extensions = ('.py', '.bat', '.html', '.css', '.js', '.json', '.md', '.env', '.txt')
    
    for root, dirs, files in os.walk(base_dir):
        if '.venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(extensions):
                path = os.path.join(root, file)
                replace_in_file(path, "Laura", "Laura")

if __name__ == "__main__":
    main()
