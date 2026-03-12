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
    "bioplex_hct116": DATA_DIR / "bioplex_hct116.tsv"
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
