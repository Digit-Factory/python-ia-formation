"""
Injecte automatiquement un bandeau "Ressources de cette notion" en haut de 
chaque fichier .qmd de notion, après le front-matter YAML.

Le bandeau contient :
- Un lien de téléchargement direct du notebook _ELEVE.ipynb
- Un lien "Ouvrir dans Colab" (si tu publies le projet sur GitHub)
- Un lien vers le ZIP complet du module

Le script est idempotent : si le bandeau est déjà présent, il est mis à jour 
plutôt que dupliqué.

Usage :
    python scripts/inject_resources_banner.py

Configuration : change GITHUB_USER et GITHUB_REPO ci-dessous.
"""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
MODULES_DIR = PROJECT_ROOT / "modules"

# === À ADAPTER SELON TON COMPTE GITHUB ===
GITHUB_USER = "Digit-Factory"          # Remplace par Loïc PILET d'utilisateur
GITHUB_REPO = "python_ia_formation"        # Remplace par le nom du repo
GITHUB_BRANCH = "main"

# Début et fin du bandeau (marqueurs pour détecter s'il existe déjà)
BANNER_START = "<!-- RESOURCES_BANNER_START -->"
BANNER_END = "<!-- RESOURCES_BANNER_END -->"


def build_banner(module_name: str, notion_filename: str) -> str:
    """Construit le bandeau pour une notion donnée."""
    notebook_name = notion_filename.replace('.qmd', '_ELEVE.ipynb')
    zip_name = f"{module_name}_ressources_eleve.zip"
    
    # URLs
    notebook_url_local = f"../../ressources_eleves/{module_name}/{notebook_name}"
    zip_url_local = f"../../ressources_eleves/{zip_name}"
    
    # URL Colab : Colab ouvre un notebook depuis GitHub via cette URL
    # Format : https://colab.research.google.com/github/USER/REPO/blob/BRANCH/chemin/vers/notebook.ipynb
    notebook_path_in_repo = f"ressources_eleves/{module_name}/{notebook_name}"
    colab_url = (
        f"https://colab.research.google.com/github/{GITHUB_USER}/{GITHUB_REPO}"
        f"/blob/{GITHUB_BRANCH}/{notebook_path_in_repo}"
    )
    
    banner = f"""{BANNER_START}

::: {{.callout-note appearance="simple" icon=false}}
## 📚 Tes ressources pour cette notion

<div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; margin-bottom: 10px;">
  <a href="{notebook_url_local}" class="btn btn-primary btn-sm" download>📥 Télécharger le notebook</a>
  <a href="{colab_url}" class="btn btn-outline-primary btn-sm" target="_blank">☁️ Ouvrir dans Colab</a>
  <a href="{zip_url_local}" class="btn btn-outline-secondary btn-sm" download>📦 Pack du module complet</a>
</div>

💡 **Workflow conseillé** : lis la théorie ici, puis ouvre le notebook pour faire les exercices. Quand tu bloques, reviens déplier « Voir la correction ».
:::

{BANNER_END}
"""
    return banner


def inject_banner(qmd_path: Path, module_name: str):
    """Injecte (ou met à jour) le bandeau dans un fichier .qmd."""
    content = qmd_path.read_text(encoding='utf-8')
    
    # Construire le bandeau
    banner = build_banner(module_name, qmd_path.name)
    
    # Cas 1 : le bandeau existe déjà → le remplacer
    if BANNER_START in content and BANNER_END in content:
        pattern = re.compile(
            re.escape(BANNER_START) + r'.*?' + re.escape(BANNER_END),
            re.DOTALL
        )
        new_content = pattern.sub(banner.strip(), content)
        print(f"  🔄 {qmd_path.name} (bandeau mis à jour)")
    else:
        # Cas 2 : le bandeau n'existe pas → l'ajouter après le front-matter
        if content.startswith('---'):
            end = content.find('\n---', 3)
            if end != -1:
                # Insérer après le front-matter
                insert_pos = end + 4  # longueur de "\n---\n"
                new_content = (
                    content[:insert_pos] 
                    + '\n' + banner + '\n'
                    + content[insert_pos:]
                )
            else:
                new_content = banner + '\n\n' + content
        else:
            new_content = banner + '\n\n' + content
        print(f"  ➕ {qmd_path.name} (bandeau ajouté)")
    
    qmd_path.write_text(new_content, encoding='utf-8')


def process_module(module_dir: Path):
    """Traite toutes les notions d'un module."""
    module_name = module_dir.name
    print(f"\n📦 {module_name}")
    
    qmd_files = sorted(module_dir.glob("*.qmd"))
    # On exclut index.qmd (c'est la page d'accueil du module)
    qmd_files = [f for f in qmd_files if f.name != "index.qmd"]
    
    for qmd_file in qmd_files:
        inject_banner(qmd_file, module_name)


def main():
    print("🚀 Injection des bandeaux de ressources\n")
    
    if GITHUB_USER == "ton-compte-github":
        print("⚠️  Pense à configurer GITHUB_USER et GITHUB_REPO dans le script")
        print("   (sinon les liens Colab ne fonctionneront pas)\n")
    
    for module_dir in sorted(MODULES_DIR.glob("module_*")):
        if module_dir.is_dir():
            process_module(module_dir)
    
    print(f"\n✨ Terminé !")
    print(f"\n📌 Prochaine étape : 'quarto render' pour régénérer le site")


if __name__ == "__main__":
    main()
