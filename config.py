import os
import shutil
import uuid
import data_loader
from pathlib import Path

# Configuration
HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
WWW_DIR = HERE / "www"
STATIC_DIR = WWW_DIR / "static"
MAP_FILE = DATA_DIR / "HuRI_BioPlex_id_map.csv"
CSS_FILE = WWW_DIR / "styles.css"

# Dataset Paths
DATASETS = {
    "huri": DATA_DIR / "huri_ppi.csv",
    "bioplex_293": DATA_DIR / "bioplex_293.tsv",
    "bioplex_hct116": DATA_DIR / "bioplex_hct116.tsv",
    "pancov": DATA_DIR / "v2_edge.xlsx",
    "husci": DATA_DIR / "HuSCI_PPIs.xlsx",
    "bacterial": DATA_DIR / "bacterial_ppi.xlsx",
    "intact": DATA_DIR / "intact_human_physical_hq_20260217.csv"
}

# Official Display Names
DATASET_ABBR = {
    "huri": "HuRI",
    "bioplex_293": "BioPlex_HEK293T",
    "bioplex_hct116": "BioPlex_HCT116",
    "pancov": "Pan-coronavirus",
    "husci": "HuSCI",
    "bacterial": "HuMMI",
    "intact": "IntAct"
}

DATASET_FULL = {
    "huri": "The Human Reference Interactome, HuRI",
    "bioplex_293": "The Biophysical Interactions of ORFeome-based Complexes Network, BioPlex_HEK293T",
    "bioplex_hct116": "BioPlex_HCT116",
    "pancov": "Pan-coronavirus",
    "husci": "SARS-CoV-2-Human Contactome, HuSCI",
    "bacterial": "The Human-Microbiome Meta-Interactome, HuMMI",
    "intact": "IntAct Human Physical HQ Interactome (2026-02-17)",
    "mygene": "Human gene nomenclature (MyGene.info)"
}

def init_workspace():
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    WWW_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)

    # Copy assets
    _LIB_SRC = HERE / "lib"
    _LIB_DEST = STATIC_DIR / "lib"
    if _LIB_SRC.exists():
        shutil.copytree(_LIB_SRC, _LIB_DEST, dirs_exist_ok=True)

def cleanup_old_graphs():
    for p in STATIC_DIR.glob("ppi_subnetwork_*.html"):
        try: p.unlink()
        except: pass
    for p in STATIC_DIR.glob("ppi_genelist_*.html"):
        try: p.unlink()
        except: pass

# Dataset colors for merged view
DATASET_COLORS = {
    "huri": "#3498db",        # Blue
    "bioplex_293": "#e74c3c", # Red
    "bioplex_hct116": "#2ecc71", # Green
    "pancov": "#f1c40f",      # Yellow
    "husci": "#9b59b6",       # Purple
    "bacterial": "#e67e22",   # Orange
    "intact": "#16a085"       # Deep Teal
}

# Global Data Cache
GLOBAL_DATA = {}
STATS = {}

def load_global_data():
    global GLOBAL_DATA, STATS
    for key, path in DATASETS.items():
        if path.exists():
            df = data_loader.load_ppi_data(str(path), str(MAP_FILE))
            GLOBAL_DATA[key] = df
            STATS[key] = data_loader.get_summary_stats(df)
