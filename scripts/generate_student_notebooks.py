"""
Génère les notebooks Jupyter "élève" à partir des fichiers .qmd.

Cette version NE nécessite PAS Quarto installé : la conversion .qmd → .ipynb 
est faite directement en Python avec nbformat.

Workflow :
1. Parcourt les .qmd de chaque module
2. Pour chaque fichier, crée une version "élève" où :
   - Les blocs de correction sont remplacés par un rappel vers le site web
   - Les cellules `pd.read_csv('ressources_tp/...')` sont précédées 
     automatiquement d'une cellule de téléchargement Colab-friendly
3. Génère le .ipynb directement
4. Range tout dans ressources_eleves/ par module, avec le dataset associé
5. Crée un ZIP téléchargeable par module

Usage :
    python scripts/generate_student_notebooks.py
    
Prérequis :
    pip install nbformat
"""

import re
import shutil
from pathlib import Path

import nbformat as nbf


# === CONFIGURATION ===
PROJECT_ROOT = Path(__file__).parent.parent
MODULES_DIR = PROJECT_ROOT / "modules"
OUTPUT_DIR = PROJECT_ROOT / "ressources_eleves"

# Pour construire les URLs de téléchargement des datasets (Colab-friendly)
GITHUB_USER = "Digit-Factory"
GITHUB_REPO = "python-ia-formation"
GITHUB_BRANCH = "main"


# === PARSING DU QMD ===

def parse_qmd(content: str):
    """Parse un fichier .qmd et retourne une liste de cellules."""
    # Retirer le front-matter YAML
    if content.startswith('---'):
        end = content.find('\n---', 3)
        if end != -1:
            content = content[end + 4:].lstrip('\n')
    
    # Retirer le bandeau de ressources (inutile dans le notebook)
    content = re.sub(
        r'<!-- RESOURCES_BANNER_START -->.*?<!-- RESOURCES_BANNER_END -->\n*',
        '',
        content,
        flags=re.DOTALL
    )
    
    cells = []
    lines = content.split('\n')
    i = 0
    current_md = []
    
    def flush_markdown():
        if current_md:
            md_text = '\n'.join(current_md).strip()
            if md_text:
                cells.append({"type": "markdown", "source": md_text})
            current_md.clear()
    
    while i < len(lines):
        line = lines[i]
        
        # --- Bloc de correction à supprimer ---
        if re.match(r':::\s*\{\.callout-tip\s+collapse="true"\}', line):
            is_solution = False
            for j in range(i+1, min(i+5, len(lines))):
                if re.search(r'##\s+.*(correction|Corrigé|corrigé)', lines[j], re.IGNORECASE):
                    is_solution = True
                    break
            
            if is_solution:
                flush_markdown()
                cells.append({
                    "type": "markdown",
                    "source": "> 💡 **Tu bloques ?** Consulte la correction sur le site web du cours en dépliant le bloc « Voir la correction »."
                })
                depth = 1
                i += 1
                while i < len(lines) and depth > 0:
                    if re.match(r':::\s*\{', lines[i]):
                        depth += 1
                    elif re.match(r':::\s*$', lines[i]):
                        depth -= 1
                    i += 1
                continue
        
        # --- Bloc de code Python ---
        code_match = re.match(r'^```\{python\}(.*)$', line)
        if code_match:
            flush_markdown()
            
            code_lines = []
            options = {}
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_line = lines[i]
                opt_match = re.match(r'#\|\s*(\w+):\s*(.*)', code_line)
                if opt_match:
                    key, value = opt_match.group(1), opt_match.group(2).strip()
                    options[key] = value
                else:
                    code_lines.append(code_line)
                i += 1
            i += 1  # sauter le ```
            
            code_content = '\n'.join(code_lines).strip('\n')
            cells.append({
                "type": "code",
                "source": code_content,
                "options": options
            })
            continue
        
        # --- Markdown normal ---
        line = convert_callouts_for_notebook(line)
        current_md.append(line)
        i += 1
    
    flush_markdown()
    return cells


def convert_callouts_for_notebook(line: str) -> str:
    """Convertit la syntaxe Quarto en markdown plus lisible dans Jupyter."""
    line = re.sub(r':::\s*\{\.callout-note[^}]*\}', '> **ℹ️ Note**\n>', line)
    line = re.sub(r':::\s*\{\.callout-tip[^}]*\}', '> **💡 Astuce**\n>', line)
    line = re.sub(r':::\s*\{\.callout-warning[^}]*\}', '> **⚠️ Attention**\n>', line)
    line = re.sub(r':::\s*\{\.callout-important[^}]*\}', '> **🎯 Important**\n>', line)
    line = re.sub(r':::\s*\{\.callout-[^}]*\}', '>', line)
    line = re.sub(r'^:::$', '', line)
    return line


# === INJECTION AUTOMATIQUE DE LA CELLULE DE TÉLÉCHARGEMENT ===

# Regex pour détecter un read_csv / read_excel / read_json / etc.
# sur un fichier local dans ressources_tp/ ou ressources/
DATASET_READ_PATTERN = re.compile(
    r"(?:pd\.read_\w+|np\.loadtxt|np\.genfromtxt|open)"
    r"\s*\(\s*['\"](ressources[_\w]*/[\w\./-]+\.[\w]+)['\"]",
    re.MULTILINE
)


def extract_dataset_references(code: str) -> set:
    """Trouve tous les fichiers datasets référencés dans le code."""
    matches = DATASET_READ_PATTERN.findall(code)
    return set(matches)


def build_download_cell(dataset_paths: set, module_name: str) -> str:
    """Construit une cellule de téléchargement pour les datasets donnés."""
    lines = ["# 📥 Téléchargement automatique des datasets (utile pour Colab)",
             "import os, urllib.request",
             ""]
    
    for dataset_path in sorted(dataset_paths):
        # Séparer le dossier et le nom de fichier
        dataset_dir = os.path.dirname(dataset_path)
        filename = os.path.basename(dataset_path)
        
        # URL raw GitHub pour ce dataset
        raw_url = (
            f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}"
            f"/{GITHUB_BRANCH}/ressources_eleves/{module_name}/{dataset_path}"
        )
        
        lines.append(f"if not os.path.exists('{dataset_path}'):")
        lines.append(f"    os.makedirs('{dataset_dir}', exist_ok=True)")
        lines.append(f"    urllib.request.urlretrieve(")
        lines.append(f"        '{raw_url}',")
        lines.append(f"        '{dataset_path}'")
        lines.append(f"    )")
        lines.append(f"    print(f\"✅ Dataset téléchargé : {filename}\")")
        lines.append(f"else:")
        lines.append(f"    print(f\"✅ Dataset déjà présent : {filename}\")")
        lines.append("")
    
    return '\n'.join(lines).strip()


# Pour l'os.path on a besoin de l'import
import os


def inject_download_cells(cells: list, module_name: str) -> list:
    """
    Parcourt les cellules, détecte les lectures de datasets, et injecte 
    une cellule de téléchargement JUSTE AVANT la première utilisation.
    
    On ne l'injecte qu'une seule fois par notebook, pour tous les datasets détectés.
    """
    # Premier passage : trouver tous les datasets référencés
    all_datasets = set()
    first_read_idx = None
    
    for idx, cell in enumerate(cells):
        if cell["type"] == "code":
            datasets_in_cell = extract_dataset_references(cell["source"])
            if datasets_in_cell and first_read_idx is None:
                first_read_idx = idx
            all_datasets.update(datasets_in_cell)
    
    if not all_datasets:
        return cells  # pas de datasets, rien à faire
    
    # Construire la cellule de téléchargement
    download_cell_code = build_download_cell(all_datasets, module_name)
    download_cell = {"type": "code", "source": download_cell_code}
    
    # Ajouter un commentaire markdown au-dessus pour expliquer
    explanation_cell = {
        "type": "markdown",
        "source": (
            "## 📥 Préparation : téléchargement des données\n\n"
            "La cellule ci-dessous télécharge automatiquement les datasets nécessaires "
            "si ils ne sont pas déjà présents localement. Cela permet de faire marcher "
            "le notebook **aussi bien en local qu'en Google Colab**."
        )
    }
    
    # Insérer AVANT la première lecture
    new_cells = (
        cells[:first_read_idx] 
        + [explanation_cell, download_cell] 
        + cells[first_read_idx:]
    )
    
    return new_cells


# === GÉNÉRATION DU NOTEBOOK ===

def build_notebook(cells):
    """Construit un notebook Jupyter."""
    nb = nbf.v4.new_notebook()
    nb_cells = []
    
    for cell in cells:
        if cell["type"] == "markdown":
            nb_cells.append(nbf.v4.new_markdown_cell(cell["source"]))
        elif cell["type"] == "code":
            nb_cells.append(nbf.v4.new_code_cell(cell["source"]))
    
    nb['cells'] = nb_cells
    nb['metadata'] = {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'name': 'python',
            'version': '3.11'
        }
    }
    return nb


# === TRAITEMENT D'UN MODULE ===

def process_module(module_dir: Path):
    """Traite un module complet."""
    module_name = module_dir.name
    print(f"\n📦 {module_name}")
    
    output_module_dir = OUTPUT_DIR / module_name
    output_module_dir.mkdir(parents=True, exist_ok=True)
    
    qmd_files = sorted(module_dir.glob("*.qmd"))
    qmd_files = [f for f in qmd_files if f.name != "index.qmd"]
    
    for qmd_file in qmd_files:
        content = qmd_file.read_text(encoding='utf-8')
        cells = parse_qmd(content)
        
        # ⭐ NOUVEAU : injection auto de la cellule de téléchargement si besoin
        cells = inject_download_cells(cells, module_name)
        
        notebook = build_notebook(cells)
        
        output_ipynb = output_module_dir / (qmd_file.stem + "_ELEVE.ipynb")
        with open(output_ipynb, 'w', encoding='utf-8') as f:
            nbf.write(notebook, f)
        
        # Indiquer si on a ajouté une cellule de téléchargement
        has_download = any(
            c["type"] == "code" and "urlretrieve" in c["source"] 
            for c in cells
        )
        suffix = " + cellule auto-download" if has_download else ""
        print(f"  ✅ {output_ipynb.name} ({len(cells)} cellules{suffix})")
    
    # Copier les ressources (datasets)
    for ressources_dir in module_dir.glob("ressources*"):
        if ressources_dir.is_dir():
            dest = output_module_dir / ressources_dir.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(ressources_dir, dest)
            print(f"  📂 {ressources_dir.name}/ copié")
    
    # README
    readme_path = output_module_dir / "README.md"
    readme_path.write_text(build_readme(module_name), encoding='utf-8')
    print(f"  📝 README.md")


def build_readme(module_name: str) -> str:
    return f"""# {module_name.replace('_', ' ').title()} — Ressources élève

Ce dossier contient tout ce dont tu as besoin pour faire les exercices du module 
en autonomie.

## 📁 Contenu

- **Notebooks Jupyter** (`*_ELEVE.ipynb`) : un par notion, avec les exercices à faire
- **Datasets** (dossier `ressources_tp/` si présent) : les données pour les TP
- **README** (ce fichier)

## 🚀 Workflow recommandé

1. **Lis la théorie sur le site web du cours** (plus agréable à lire)
2. **Ouvre le notebook de la notion** dans Jupyter Lab / VS Code
3. **Travaille les exercices** dans les cellules `# TODO`
4. **Si tu bloques**, retourne sur le site web → déplie « Voir la correction »

## 🛠️ Prérequis

```bash
pip install jupyter numpy pandas matplotlib seaborn scipy
```

## 💡 Colab prêt à l'emploi

Les notebooks ayant besoin d'un dataset contiennent une cellule qui **télécharge 
automatiquement** les données nécessaires depuis GitHub. Tu peux donc les ouvrir 
dans Google Colab directement depuis le site du cours, sans rien configurer.

## 💡 Conseils

- **Ne saute pas les exercices** : la compréhension vient en faisant.
- **Résiste à la tentation** de regarder la correction trop vite (donne-toi 
  au moins 30 minutes de réflexion).

Bon courage ! 🚀
"""


def create_module_zip(module_name: str):
    """Zippe le dossier ressources d'un module."""
    zip_basename = OUTPUT_DIR / f"{module_name}_ressources_eleve"
    zip_file = zip_basename.with_suffix('.zip')
    if zip_file.exists():
        zip_file.unlink()
    
    shutil.make_archive(
        str(zip_basename),
        'zip',
        root_dir=str(OUTPUT_DIR),
        base_dir=module_name
    )
    size_kb = zip_file.stat().st_size / 1024
    print(f"  📦 {zip_file.name} ({size_kb:.1f} KB)")


def main():
    print("🚀 Génération des notebooks élèves")
    print(f"   GitHub : {GITHUB_USER}/{GITHUB_REPO} (branche {GITHUB_BRANCH})\n")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    for module_dir in sorted(MODULES_DIR.glob("module_*")):
        if module_dir.is_dir():
            process_module(module_dir)
            create_module_zip(module_dir.name)
    
    print(f"\n✨ Terminé !")
    print(f"📂 Ressources dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
