"""
Génère le dataset d'images de pièces industrielles pour le TP sommatif Module 6.

Contexte : 
    Startup MetalCheck qui fait du contrôle qualité automatisé.
    3 classes de pièces métalliques :
    - ok      : pièce sans défaut (400 images)
    - rayure  : pièce avec rayures superficielles (80 images)
    - fissure : pièce avec fissure critique (40 images)

Dataset volontairement DÉSÉQUILIBRÉ (comme en vrai projet) pour enseigner :
    - la gestion du déséquilibre de classes
    - la pondération de la loss
    - l'importance du recall sur les classes rares (sécurité)

Images :
    - 224x224 RGB
    - Déjà split train/test (80/20)
    - Structure compatible ImageFolder de torchvision

Usage :
    python scripts/generate_module_06_dataset.py
    python scripts/generate_module_06_dataset.py --output /chemin/perso
    python scripts/generate_module_06_dataset.py --seed 2025 --force
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# === Configuration par défaut ===
DEFAULT_OUTPUT = Path(__file__).parent.parent / "modules" / "module_06" / "ressources_tp" / "pieces"
IMAGE_SIZE = 224
N_PAR_CLASSE = {
    "ok": 400,       # 77% - cas normal, abondant
    "rayure": 80,    # 15% - défaut fréquent
    "fissure": 40,   # 8%  - défaut rare mais critique
}
SPLIT_TRAIN_RATIO = 0.8  # 80% train, 20% test


def image_base(rng):
    """Crée une pièce métallique de base (cercle gris sur fond sombre).
    
    Retourne :
        tuple (PIL.Image, cx, cy, r) : image + coords du centre + rayon
    """
    # Fond sombre avec bruit gaussien
    bg_color = rng.integers(25, 55)
    img_array = np.full((IMAGE_SIZE, IMAGE_SIZE, 3), bg_color, dtype=np.uint8)
    noise = rng.normal(0, 8, (IMAGE_SIZE, IMAGE_SIZE, 3))
    img_array = np.clip(img_array.astype(float) + noise, 0, 255).astype(np.uint8)
    
    pil_img = Image.fromarray(img_array)
    draw = ImageDraw.Draw(pil_img)
    
    # Position et rayon de la pièce (variations pour augmenter la diversité)
    cx = IMAGE_SIZE // 2 + rng.integers(-15, 16)
    cy = IMAGE_SIZE // 2 + rng.integers(-15, 16)
    r = rng.integers(70, 96)
    
    # Couleur métallique de base (variations entre pièces)
    metal_base = rng.integers(140, 186)
    
    # Gradient radial pour effet 3D (reflet au centre)
    for i in range(r, 0, -1):
        ratio = i / r
        color_val = int(metal_base + (1 - ratio) * 30 - ratio * 15)
        color_val = max(60, min(220, color_val))
        # Légère teinte bleutée aléatoire pour réalisme
        draw.ellipse(
            [cx - i, cy - i, cx + i, cy + i],
            fill=(color_val, color_val, color_val + int(rng.integers(-5, 6)))
        )
    
    return pil_img, cx, cy, r


def image_ok(rng):
    """Pièce sans défaut : juste la base, éventuellement légèrement floue."""
    img, _, _, _ = image_base(rng)
    if rng.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.5, 1.2))))
    return img


def image_rayure(rng):
    """Pièce avec 2 à 4 rayures : lignes droites sombres."""
    img, cx, cy, r = image_base(rng)
    draw = ImageDraw.Draw(img)
    
    n_rayures = int(rng.integers(2, 5))
    for _ in range(n_rayures):
        angle = float(rng.uniform(0, 2 * np.pi))
        longueur = int(rng.integers(30, 81))
        x1 = cx + int(rng.integers(-r // 2, r // 2 + 1))
        y1 = cy + int(rng.integers(-r // 2, r // 2 + 1))
        x2 = x1 + int(longueur * np.cos(angle))
        y2 = y1 + int(longueur * np.sin(angle))
        
        couleur = int(rng.integers(30, 71))
        epaisseur = int(rng.integers(1, 4))
        draw.line([x1, y1, x2, y2], fill=(couleur, couleur, couleur), width=epaisseur)
    
    if rng.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.3, 0.8))))
    return img


def image_fissure(rng):
    """Pièce avec fissure : motif branchu sombre (structure dendritique fractale)."""
    img, cx, cy, r = image_base(rng)
    draw = ImageDraw.Draw(img)
    
    def trace_branche(x, y, angle, longueur, profondeur=0):
        """Trace récursivement une branche avec ramifications."""
        if profondeur > 3 or longueur < 5:
            return
        x2 = x + int(longueur * np.cos(angle))
        y2 = y + int(longueur * np.sin(angle))
        couleur = int(rng.integers(15, 46))
        epaisseur = max(1, 3 - profondeur)
        draw.line([x, y, x2, y2], fill=(couleur, couleur, couleur), width=epaisseur)
        
        # Ramifications aléatoires
        if rng.random() < 0.7:
            trace_branche(x2, y2, angle + float(rng.uniform(-0.8, -0.2)),
                          longueur * 0.6, profondeur + 1)
        if rng.random() < 0.7:
            trace_branche(x2, y2, angle + float(rng.uniform(0.2, 0.8)),
                          longueur * 0.6, profondeur + 1)
    
    # Point de départ à l'intérieur de la pièce
    start_x = cx + int(rng.integers(-r // 3, r // 3 + 1))
    start_y = cy + int(rng.integers(-r // 3, r // 3 + 1))
    angle_init = float(rng.uniform(0, 2 * np.pi))
    trace_branche(start_x, start_y, angle_init, int(rng.integers(40, 71)))
    
    if rng.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.3, 0.8))))
    return img


# Mapping classe → fonction génératrice
GENERATORS = {
    "ok": image_ok,
    "rayure": image_rayure,
    "fissure": image_fissure,
}


def generate_dataset(output_dir: Path, seed: int = 2025, force: bool = False) -> dict:
    """Génère le dataset complet.
    
    Args:
        output_dir : Dossier de sortie (sera créé)
        seed : Graine aléatoire pour reproductibilité
        force : Si True, écrase un dataset existant
    
    Returns:
        dict : Statistiques de génération (counts par split/classe)
    """
    # Vérifier si déjà présent
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError(
            f"Le dossier {output_dir} existe déjà et n'est pas vide. "
            f"Utilise --force pour écraser."
        )
    
    # Nettoyer si force
    if output_dir.exists() and force:
        shutil.rmtree(output_dir)
    
    rng = np.random.default_rng(seed)
    stats = {}
    
    for classe, n_total in N_PAR_CLASSE.items():
        n_train = int(n_total * SPLIT_TRAIN_RATIO)
        n_test = n_total - n_train
        
        for split, n in [("train", n_train), ("test", n_test)]:
            dir_classe = output_dir / split / classe
            dir_classe.mkdir(parents=True, exist_ok=True)
            
            for i in range(n):
                img = GENERATORS[classe](rng)
                img.save(dir_classe / f"{classe}_{i:04d}.jpg", quality=85)
            
            stats.setdefault(split, {})[classe] = n
        
        print(f"  ✅ {classe:10s} : {n_train} train + {n_test} test = {n_total}")
    
    return stats


def print_summary(output_dir: Path, stats: dict) -> None:
    """Affiche un récapitulatif clair après génération."""
    print(f"\n📁 Dossier : {output_dir}")
    
    total = sum(n for split_stats in stats.values() for n in split_stats.values())
    print(f"✅ Total : {total} images générées\n")
    
    # Tableau de répartition
    print("=== Répartition ===")
    print(f"{'Classe':<12} {'Train':>7} {'Test':>7} {'Total':>7}")
    print("-" * 35)
    for classe in N_PAR_CLASSE:
        tr = stats["train"][classe]
        te = stats["test"][classe]
        print(f"{classe:<12} {tr:>7} {te:>7} {tr+te:>7}")
    print("-" * 35)
    tot_tr = sum(stats["train"].values())
    tot_te = sum(stats["test"].values())
    print(f"{'TOTAL':<12} {tot_tr:>7} {tot_te:>7} {tot_tr+tot_te:>7}")
    
    # Déséquilibre
    print("\n=== Déséquilibre (train) ===")
    for classe in N_PAR_CLASSE:
        pct = stats["train"][classe] / tot_tr * 100
        print(f"  {classe:<12} : {pct:5.1f}%")


def parse_args():
    """Parse les arguments CLI."""
    parser = argparse.ArgumentParser(
        description="Génère le dataset d'images pour le TP sommatif Module 6.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Dossier de sortie (défaut : {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2025,
        help="Graine aléatoire pour reproductibilité (défaut : 2025)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Écrase un dataset existant"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("=== Génération dataset Module 6 — Pièces industrielles ===\n")
    print(f"🎯 Sortie : {args.output}")
    print(f"🎲 Seed   : {args.seed}\n")
    
    try:
        stats = generate_dataset(args.output, seed=args.seed, force=args.force)
    except FileExistsError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    
    print_summary(args.output, stats)
    print("\n✨ Terminé !")


if __name__ == "__main__":
    main()
