import os
import urllib.request

def download_montserrat():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "assets", "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    
    # URL direta para Montserrat Black do repositório oficial do Google Fonts no GitHub
    url = "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Black.ttf"
    target_path = os.path.join(fonts_dir, "Montserrat-Black.ttf")
    
    if not os.path.exists(target_path):
        print(f"Baixando fonte de {url}...")
        try:
            urllib.request.urlretrieve(url, target_path)
            print("Fonte baixada com sucesso!")
        except Exception as e:
            print(f"Erro ao baixar fonte: {e}")
            # Tentar baixar do sistema como fallback (windows) ou usar a fonte padrao
            print("Fallback ativado. Utilize o arial.ttf nativo caso este falhe.")
    else:
        print("A fonte já existe na pasta.")

if __name__ == "__main__":
    download_montserrat()
