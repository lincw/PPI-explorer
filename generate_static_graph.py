import sys
import os
import data_loader
import graph_utils
import shutil
from pathlib import Path

def generate_static_html(gene_symbol, dataset_key, output_filename=None):
    # Configuration matches app.py
    HERE = Path(__file__).parent
    DATA_DIR = HERE / "data"
    WWW_DIR = HERE / "www"
    STATIC_DIR = WWW_DIR / "static"
    MAP_FILE = DATA_DIR / "HuRI_BioPlex_id_map.csv"

    DATASETS = {
        "huri": DATA_DIR / "huri_ppi.csv",
        "bioplex_293": DATA_DIR / "bioplex_293.tsv",
        "bioplex_hct116": DATA_DIR / "bioplex_hct116.tsv"
    }

    if dataset_key not in DATASETS:
        print(f"Error: Dataset '{dataset_key}' not found. Choose from: {list(DATASETS.keys())}")
        return

    data_path = DATASETS[dataset_key]
    if not data_path.exists():
        print(f"Error: Data file {data_path} does not exist.")
        return

    print(f"Loading {dataset_key} data...")
    df = data_loader.load_ppi_data(str(data_path), str(MAP_FILE))

    print(f"Finding neighbors for {gene_symbol}...")
    sub_df = data_loader.get_subnetwork(df, [gene_symbol])

    if sub_df.empty:
        print(f"No interactions found for {gene_symbol} in {dataset_key}.")
        return

    print(f"Generating graph...")
    # This creates a temporary HTML file
    tmp_file = graph_utils.create_subnetwork_graph(sub_df, {gene_symbol.upper()})

    if not tmp_file or not os.path.exists(tmp_file):
        print("Error: Failed to generate graph HTML.")
        return

    # Post-process for standalone/Nginx use
    with open(tmp_file, "r") as f:
        html = f.read()
    
    # Remove local script dependency for cleaner standalone serving
    html = html.replace('<script src="lib/bindings/utils.js"></script>', "")
    
    with open(tmp_file, "w") as f:
        f.write(html)

    if output_filename is None:
        output_filename = f"static_graph_{dataset_key}_{gene_symbol}.html"

    # Ensure output directory exists if provided in filename
    output_path = Path(output_filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy(tmp_file, output_filename)
    print(f"Successfully created static graph: {output_filename}")
    print(f"To serve with Nginx, just place this file in your web root.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_static_graph.py <GENE_SYMBOL> <DATASET_KEY> [OUTPUT_FILENAME]")
        print("Example: python generate_static_graph.py BRCA1 bioplex_293 my_graph.html")
    else:
        gene = sys.argv[1]
        dataset = sys.argv[2]
        out_file = sys.argv[3] if len(sys.argv) > 3 else None
        generate_static_html(gene, dataset, out_file)
