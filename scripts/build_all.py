"""
Script maître : construit toutes les ressources élèves en un coup.

Enchaîne :
1. Génération des notebooks élèves (depuis les .qmd)
2. Injection des bandeaux de ressources dans les .qmd
3. Création des ZIP par module
4. (optionnel) Rendu Quarto si quarto est installé

Usage :
    python scripts/build_all.py
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_script(script_name: str, description: str):
    """Exécute un script Python et affiche son output."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    script_path = SCRIPTS_DIR / script_name
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT)
    )
    
    if result.returncode != 0:
        print(f"❌ Erreur lors de {script_name}")
        sys.exit(1)


def run_quarto_render():
    """Lance quarto render si Quarto est installé."""
    try:
        subprocess.run(['quarto', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n⏭️  Quarto non installé — le site ne sera pas régénéré.")
        print("   (installe Quarto pour automatiser aussi cette étape)")
        return
    
    print(f"\n{'='*60}")
    print("🔧 Rendu Quarto du site")
    print(f"{'='*60}")
    
    subprocess.run(['quarto', 'render'], cwd=str(PROJECT_ROOT))


def main():
    print("🚀 Build complet des ressources élèves")
    
    # 1. Injecter les bandeaux dans les .qmd
    run_script(
        "inject_resources_banner.py",
        "Étape 1/3 — Injection des bandeaux de ressources dans les .qmd"
    )
    
    # 2. Générer les notebooks élèves + ZIP
    run_script(
        "generate_student_notebooks.py",
        "Étape 2/3 — Génération des notebooks élèves et des ZIP"
    )
    
    # 3. Rendre le site (optionnel)
    print(f"\n{'='*60}")
    print("🔧 Étape 3/3 — Rendu du site (optionnel)")
    print(f"{'='*60}")
    run_quarto_render()
    
    print(f"\n{'='*60}")
    print("✨ Build terminé !")
    print(f"{'='*60}")
    print("\n📂 Les ressources élèves sont dans : ressources_eleves/")
    print("📂 Le site est dans : _build/")
    print("\n📌 Pour publier :")
    print("   - GitHub Pages : git add . && git commit && git push")
    print("   - Ou : quarto publish")


if __name__ == "__main__":
    main()
