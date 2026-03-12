import pandas as pd
import os

def load_ppi_data(file_path, map_file_path=None):
    """
    Loads PPI data and optionally merges with Ensembl IDs.
    Supports .csv and .tsv files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Determine separator based on extension
    sep = '\t' if file_path.endswith('.tsv') else ','
    df = pd.read_csv(file_path, sep=sep)
    
    # Standardize column names
    if 'SymbolA' in df.columns and 'SymbolB' in df.columns:
        # BioPlex format
        df = df.rename(columns={'SymbolA': 'from', 'SymbolB': 'to'})
        if 'original_SymbolA' in df.columns and 'original_SymbolB' in df.columns:
            df = df.rename(columns={'original_SymbolA': 'original_from', 'original_SymbolB': 'original_to'})
    elif 'from' not in df.columns or 'to' not in df.columns:
        # Generic rename for other formats
        rename_map = {
            'GeneA': 'from', 'GeneB': 'to',
            'InteractorA': 'from', 'InteractorB': 'to'
        }
        df = df.rename(columns=rename_map)
    
    # Keep only necessary columns
    cols_to_keep = ['from', 'to']
    if 'original_from' in df.columns and 'original_to' in df.columns:
        cols_to_keep.extend(['original_from', 'original_to'])
    
    df = df[cols_to_keep]
    
    if map_file_path and os.path.exists(map_file_path):
        # Load map: HGNC -> ensemblID, UniprotID
        map_df = pd.read_csv(map_file_path, usecols=["HGNC", "ensemblID", "UniprotID"])
        
        # Rename to match internal logic
        map_df = map_df.rename(columns={
            "HGNC": "hgnc_symbol",
            "ensemblID": "ensembl_gene_id",
            "UniprotID": "uniprot"
        })
        
        # Replace empty strings or whitespace-only strings with NaN for proper filling
        map_df = map_df.replace(r"^\s*$", pd.NA, regex=True)
        
        # Drop duplicates to avoid many-to-many merge issues
        map_df = map_df.drop_duplicates(subset=["hgnc_symbol"])
        
        # Merge for 'from' column
        df = df.merge(map_df, left_on="from", right_on="hgnc_symbol", how="left")
        df = df.rename(columns={"ensembl_gene_id": "from_ensembl", "uniprot": "from_uniprot"}).drop(columns=["hgnc_symbol"])
        
        # Merge for 'to' column
        df = df.merge(map_df, left_on="to", right_on="hgnc_symbol", how="left")
        df = df.rename(columns={"ensembl_gene_id": "to_ensembl", "uniprot": "to_uniprot"}).drop(columns=["hgnc_symbol"])
        
    return df

def get_neighbors(df, query_gene):
    """
    Returns a sub-DataFrame containing all interactions involving the query_gene.
    Matches against both current and original gene symbols if available.
    """
    # Case-insensitive search
    query_gene = str(query_gene).strip().upper()
    
    # Base masks for current symbols
    mask = (df['from'].str.upper() == query_gene) | (df['to'].str.upper() == query_gene)
    
    # Also check original symbols if they exist in the dataframe
    if 'original_from' in df.columns:
        mask |= (df['original_from'].str.upper() == query_gene)
    if 'original_to' in df.columns:
        mask |= (df['original_to'].str.upper() == query_gene)
        
    return df[mask]

def get_summary_stats(df):
    """
    Calculates summary statistics for the PPI dataset.
    """
    if df.empty:
        return {}
    
    num_interactions = len(df)
    unique_genes = pd.concat([df['from'], df['to']]).unique()
    num_genes = len(unique_genes)
    
    # Calculate degree (number of connections) for each gene
    all_genes_series = pd.concat([df['from'], df['to']])
    degree_counts = all_genes_series.value_counts()
    avg_degree = degree_counts.mean()
    max_degree = degree_counts.max()
    top_hub = degree_counts.index[0]
    
    return {
        "num_interactions": num_interactions,
        "num_genes": num_genes,
        "avg_degree": round(avg_degree, 2),
        "max_degree": int(max_degree),
        "top_hub": top_hub
    }

def get_unique_genes(df):
    """
    Returns a sorted list of unique genes in the PPI dataset.
    """
    all_genes = pd.concat([df['from'], df['to']]).unique()
    return sorted([str(g) for g in all_genes])
