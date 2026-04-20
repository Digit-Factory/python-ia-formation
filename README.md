# 🐍 Python pour l'IA — Projet Quarto

Parcours de formation complet en Python pour l'intelligence artificielle, construit avec [Quarto](https://quarto.org).

## 🎯 Ce que tu obtiens avec ce projet

À partir d'**un seul fichier source** (`.qmd`) par notion, Quarto génère automatiquement :

- 🌐 **Un site web** complet avec navigation, recherche, thème clair/sombre
- 📄 **Un PDF** imprimable par notion et un PDF global du livre
- 📓 **Des notebooks Jupyter** élèves (générés automatiquement depuis les `.qmd`)
- 📦 **Des ZIP de ressources** téléchargeables par module
- ☁️ **Des liens Google Colab** pour travailler sans rien installer

Un seul fichier source, autant de formats de sortie que tu veux.

## 🏗️ Architecture pédagogique

```
┌──────────────────────┐
│   Fichier .qmd       │  ← Tu rédiges ICI (un seul fichier source)
│   (théorie +         │
│   exercices +        │
│   corrigés cachés)   │
└──────────┬───────────┘
           │
           ▼
   ┌───────────────┐
   │   quarto      │
   │   render      │
   └───────┬───────┘
           │
  ┌────────┼─────────┬──────────────┐
  ▼        ▼         ▼              ▼
🌐 HTML  📄 PDF   📓 Notebook   📦 ZIP
 Site    imprim.   élève         module
                   (sans
                   corrigés)
```

## 📦 Installation (une seule fois)

### 1. Installer Quarto

Télécharge et installe Quarto depuis [quarto.org/docs/get-started/](https://quarto.org/docs/get-started/).

Vérifie l'installation :

```bash
quarto --version
```

### 2. Installer Python et les dépendances

```bash
pip install jupyter numpy matplotlib pandas scikit-learn nbformat
```

Pour la génération de PDF, il faut aussi LaTeX (via TinyTeX, automatique) :

```bash
quarto install tinytex
```

## 🚀 Utilisation au quotidien

### Workflow de rédaction

```bash
# 1. Rédige ou modifie un fichier .qmd dans modules/
# 2. Prévisualise en temps réel
quarto preview
```

### Workflow de publication (build complet)

Une seule commande enchaîne tout :

```bash
python scripts/build_all.py
```

Cela fait en chaîne :
1. **Injecte les bandeaux** de ressources dans chaque .qmd (boutons télécharger / Colab)
2. **Génère les notebooks élèves** depuis les .qmd (sans les corrigés)
3. **Crée les ZIP** téléchargeables par module
4. **Rend le site** avec Quarto (HTML + PDF)

### Publier le site en ligne (gratuit)

**Option 1 : GitHub Pages**

```bash
quarto publish gh-pages
```

**Option 2 : Quarto Pub**

```bash
quarto publish quarto-pub
```

## 📂 Structure du projet

```
python_ia_quarto/
├── _quarto.yml                  # Configuration globale
├── index.qmd                    # Page d'accueil
├── styles/                      # CSS personnalisé
├── modules/                     # ◉ Les fichiers sources
│   └── module_01/
│       ├── index.qmd            # Accueil du module
│       ├── notion_1_1_*.qmd     # Les notions
│       ├── tp_sommatif.qmd      # Le TP
│       └── ressources_tp/       # Datasets du TP
│           └── *.csv
├── ressources_eleves/           # 🤖 Généré par build_all.py
│   ├── module_01/
│   │   ├── *_ELEVE.ipynb        # Notebooks élèves (sans corrigés)
│   │   ├── ressources_tp/       # Datasets copiés
│   │   └── README.md
│   └── module_01_ressources_eleve.zip
├── _build/                      # 🤖 Généré par quarto render
│   ├── index.html
│   └── ...
├── scripts/                     # Scripts d'automatisation
│   ├── build_all.py             # Script maître
│   ├── generate_student_notebooks.py
│   └── inject_resources_banner.py
├── README.md                    # Ce fichier
├── requirements.txt
└── .gitignore
```

## ✍️ Ajouter une nouvelle notion

1. **Crée le fichier** : `modules/module_01/notion_1_4_ma_notion.qmd`
2. **Copie l'en-tête YAML** depuis une notion existante
3. **Rédige ta notion** avec le pattern standard :
   - Théorie + exemples de code
   - Exercices dans des `callout-note`
   - Corrections dans des `callout-tip collapse="true"` avec "correction" dans le titre
4. **Ajoute le fichier** dans `_quarto.yml` (section `chapters`)
5. **Regénère tout** : `python scripts/build_all.py`

## ⚙️ Configuration GitHub + Colab

Pour que les boutons « Ouvrir dans Colab » fonctionnent, édite 
`scripts/inject_resources_banner.py` :

```python
GITHUB_USER = "ton-compte-github"
GITHUB_REPO = "python_ia_formation"
GITHUB_BRANCH = "main"
```

Puis commit et push ton projet sur GitHub.

## 🎓 Deux versions, un seul code source

Quarto gère élégamment les versions élève/formateur via les **blocs collapsibles** :

```markdown
::: {.callout-note icon=false}
## 📝 Exercice
Fais ceci, cela...
:::

::: {.callout-tip collapse="true"}
## ✅ Voir la correction

\```{python}
# Code du corrigé
\```
:::
```

- Sur le **site web** : l'élève clique pour découvrir la correction
- Dans le **notebook téléchargé** : la correction est remplacée par un lien vers le site

## 📚 Ressources utiles

- Documentation Quarto : https://quarto.org/docs/guide/
- Guide des callout : https://quarto.org/docs/authoring/callouts.html
- Thèmes Bootswatch : https://bootswatch.com/

## ❓ Dépannage

**Problème** : `quarto preview` ne démarre pas  
**Solution** : `python -m jupyter --version` pour vérifier Jupyter

**Problème** : Le PDF ne se génère pas  
**Solution** : `quarto install tinytex`

**Problème** : Les liens Colab donnent 404  
**Solution** : Vérifie que `GITHUB_USER/REPO` est bon et que tu as bien `git push` les notebooks

**Problème** : Je veux régénérer juste les notebooks élèves  
**Solution** : `python scripts/generate_student_notebooks.py`

---

**Bonne rédaction ! 🚀**

