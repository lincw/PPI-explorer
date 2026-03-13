import pandas as pd
import os

def load_ppi_data(file_path, map_file_path=None, **kwargs):
    """
    Loads PPI data and optionally merges with Ensembl IDs.
    Supports .csv, .tsv, and .xlsx files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Determine loader based on extension
    if file_path.endswith('.xlsx'):
        # Check if it's the bacterial effector dataset which needs special handling
        if "Supplementary Data 11" in file_path and "_updated" not in file_path:
            df = pd.read_excel(file_path, sheet_name='11A', header=3)
        else:
            df = pd.read_excel(file_path, **kwargs)
    else:
        sep = '\t' if file_path.endswith('.tsv') else ','
        df = pd.read_csv(file_path, sep=sep, **kwargs)
    
    # Standardize column names
    if 'from' in df.columns and 'to' in df.columns:
        # Standard format used in updated files
        if 'original_from' not in df.columns:
            df['original_from'] = df['from']
        if 'original_to' not in df.columns:
            df['original_to'] = df['to']
    elif 'SymbolA' in df.columns and 'SymbolB' in df.columns:
        # BioPlex format
        df = df.rename(columns={'SymbolA': 'from', 'SymbolB': 'to'})
        if 'original_SymbolA' in df.columns and 'original_SymbolB' in df.columns:
            df = df.rename(columns={'original_SymbolA': 'original_from', 'original_SymbolB': 'original_to'})
        else:
            df['original_from'] = df['from']
            df['original_to'] = df['to']
    elif 'viral_protein' in df.columns and 'human_protein_HGNC' in df.columns:
        # Fallback for original pancov format
        df = df.rename(columns={'viral_protein': 'from', 'human_protein_HGNC': 'to'})
        df['original_from'] = df['from']
        df['original_to'] = df['to']
    elif 'Viral protein' in df.columns and 'Host protein' in df.columns:
        # Fallback for original HuSCI format
        df = df.rename(columns={'Viral protein': 'from', 'Host protein': 'to'})
        df['original_from'] = df['from']
        df['original_to'] = df['to']
    elif 'Human protein symbol' in df.columns and 'Effector Abbreviation' in df.columns:
        # Fallback for original Bacterial effector format
        df = df.rename(columns={'Effector Abbreviation': 'from', 'Human protein symbol': 'to'})
        df['original_from'] = df['from']
        df['original_to'] = df['to']
    elif 'from' not in df.columns or 'to' not in df.columns:
        # Generic rename for other formats
        rename_map = {
            'GeneA': 'from', 'GeneB': 'to',
            'InteractorA': 'from', 'InteractorB': 'to'
        }
        df = df.rename(columns=rename_map)
    
    # Keep only necessary columns
    cols_to_keep = ['from', 'to']
    if 'original_from' in df.columns: cols_to_keep.append('original_from')
    if 'original_to' in df.columns: cols_to_keep.append('original_to')
    
    # Check if we already have enriched columns
    enriched_cols = ['from_entrez', 'to_entrez', 'from_ensembl', 'to_ensembl', 'from_uniprot', 'to_uniprot']
    for ec in enriched_cols:
        if ec in df.columns:
            cols_to_keep.append(ec)
    
    df = df[cols_to_keep]
    
    # Only perform merge if enriched columns are missing and a map file is provided
    has_enriched = all(c in df.columns for c in enriched_cols)
    
    if not has_enriched and map_file_path and os.path.exists(map_file_path):
        # Load map: HGNC -> ensemblID, entrezID, UniprotID
        map_df = pd.read_csv(map_file_path, usecols=["HGNC", "ensemblID", "entrezID", "UniprotID"])
        
        # Drop duplicates by HGNC to avoid many-to-many merge issues
        map_df = map_df.drop_duplicates(subset=["HGNC"])
        
        # Rename to match internal logic
        map_df = map_df.rename(columns={
            "HGNC": "hgnc_symbol",
            "ensemblID": "ensembl_gene_id",
            "entrezID": "entrez_id",
            "UniprotID": "uniprot"
        })
        
        # Merge for 'from' column
        df = df.merge(map_df, left_on="from", right_on="hgnc_symbol", how="left")
        df = df.rename(columns={
            "ensembl_gene_id": "from_ensembl", 
            "entrez_id": "from_entrez",
            "uniprot": "from_uniprot"
        }).drop(columns=["hgnc_symbol"])
        
        # Merge for 'to' column
        df = df.merge(map_df, left_on="to", right_on="hgnc_symbol", how="left")
        df = df.rename(columns={
            "ensembl_gene_id": "to_ensembl", 
            "entrez_id": "to_entrez",
            "uniprot": "to_uniprot"
        }).drop(columns=["hgnc_symbol"])
        
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

def get_subnetwork(df, roots):
    """
    Returns all interactions among the roots and their first-degree neighbors.
    This includes root-neighbor AND neighbor-neighbor interactions.
    """
    if not roots:
        return pd.DataFrame(columns=df.columns)
        
    if isinstance(roots, (str, set)):
        roots = list(roots)
    
    # 1. Get all edges connected to roots
    all_results = [get_neighbors(df, r) for r in roots]
    combined = pd.concat(all_results).drop_duplicates()
    
    if combined.empty:
        return combined
        
    # 2. Identify all nodes in this 1st-degree neighborhood
    # Use the symbols as they appear in the dataset
    all_nodes = pd.concat([combined['from'], combined['to']]).unique()
    all_nodes_set = set(all_nodes)
    
    # Add roots explicitly to ensure they are included
    for r in roots:
        all_nodes_set.add(str(r).strip())
        
    # 3. Find ALL edges in the dataset where BOTH participants are in our node set
    mask = df['from'].isin(all_nodes_set) & df['to'].isin(all_nodes_set)
    final_df = df[mask].drop_duplicates()
    
    return final_df

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
