import os
import importlib.util
import sys
import unicodedata

class SkillManager:
    def __init__(self, skills_dir="skills"):
        self.skills_dir = os.path.abspath(skills_dir)
        if self.skills_dir not in sys.path:
            sys.path.append(self.skills_dir)
        self.skills = []
        self.load_skills()

    def load_skills(self):
        """Carrega dinamicamente todos os arquivos .py na pasta de skills."""
        self.skills = []
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            
        print(f"\n[SkillManager] Carregando skills de '{self.skills_dir}'...")
        
        for filename in sorted(os.listdir(self.skills_dir)):
            if filename.endswith(".py") and not filename.startswith("__"):
                skill_path = os.path.join(self.skills_dir, filename)
                skill_name = filename[:-3]
                
                try:
                    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[skill_name] = module
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, "KEYWORDS") and hasattr(module, "execute"):
                        self.skills.append(module)
                        print(f"  [OK] Skill carregada: {skill_name}")
                except Exception as e:
                    print(f"  [ERRO] Falha ao carregar {skill_name}: {e}")
        
        print(f"[SkillManager] Total de skills ativas: {len(self.skills)}\n")

    def handle(self, query, say, takeCommand, context=None):
        """
        Verifica as skills, priorizando as que têm as palavras-chave mais longas e específicas.
        """
        query_lower = query.lower()
        
        # COMANDO NATIVO: Recarregar Sistema
        if any(w in query_lower for w in ["recarregar habilidades", "atualizar habilidades", "recarregar skills", "atualizar sistema"]):
            say("Iniciando atualização do sistema de habilidades, senhor.")
            self.load_skills()
            say(f"Sistema atualizado. Agora possuo {len(self.skills)} habilidades ativas.")
            return True

        # Cria uma lista de todas as keywords de todas as skills para ordenar por tamanho
        all_matches = []
        for skill in self.skills:
            for keyword in skill.KEYWORDS:
                if keyword.lower() in query_lower:
                    all_matches.append((len(keyword), skill, keyword))
        
        # Ordena pelo tamanho da keyword (maior primeiro)
        # Isso garante que "agendar whatsapp" ganhe de "whatsapp"
        all_matches.sort(key=lambda x: x[0], reverse=True)
        
        if all_matches:
            best_match = all_matches[0]
            skill = best_match[1]
            keyword = best_match[2]
            
            try:
                print(f"[SkillManager] Melhor correspondência: '{keyword}' -> Ativando '{skill.__name__}'")
                result = skill.execute(query, say, takeCommand, context)
                # Se a skill retornar False, significa que ela recusou o comando
                if result is not False:
                    return True
            except Exception as e:
                print(f"Erro ao executar skill {skill.__name__}: {e}")
                say("Desculpe senhor, ocorreu um erro ao executar esta função.")
                return True
                
        return False
