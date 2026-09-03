import os
import subprocess

def create_desktop_shortcut():
    # Caminhos
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(current_dir, "run_laura.bat")
    
    # Comando PowerShell para detectar o desktop e criar o atalho
    ps_command = f"""
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktop "Laura AI.lnk"
    $s = (New-Object -COM WScript.Shell).CreateShortcut($shortcutPath)
    $s.TargetPath = '{target_file}'
    $s.WorkingDirectory = '{current_dir}'
    $s.Description = 'Assistente Inteligente Laura'
    $s.Save()
    Write-Host "Atalho criado em: $shortcutPath"
    """
    
    try:
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        print(f"Sucesso! Atalho criado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao criar atalho: {e}")
        return False

if __name__ == "__main__":
    create_desktop_shortcut()
