import pandas as pd
import mygene
import os

def main():
    print("Step 1: Collecting all identifiers for the comprehensive ID map...")
    
    symbols = set()
    entrez_ids = set()
    ensembl_ids = set()

    # Define all source files and their column mappings for initial collection
    # format: (path, list_of_symbol_cols, list_of_entrez_cols, list_of_ensembl_cols, extra_args)
    sources = [
        ('data/huri_ppi.csv', ['from', 'to', 'original_from', 'original_to'], [], [], {}),
        ('data/bioplex_293.tsv', ['SymbolA', 'SymbolB', 'original_SymbolA', 'original_SymbolB'], ['GeneA', 'GeneB'], [], {'sep': '\t'}),
        ('data/bioplex_hct116.tsv', ['SymbolA', 'SymbolB', 'original_SymbolA', 'original_SymbolB'], ['GeneA', 'GeneB'], [], {'sep': '\t'}),
        ('data/v2_edge.xlsx', ['human_protein_HGNC', 'viral_protein'], ['entrez'], ['ensembl_hg'], {}),
        ('data/HuSCI_PPIs.xlsx', ['Host protein', 'Viral protein'], [], [], {}),
        ('data/Supplementary Data 11.xlsx', ['Human protein symbol', 'Effector Abbreviation'], [], [], {'sheet_name': '11A', 'header': 3})
    ]

    for path, sym_cols, ent_cols, ens_cols, kwargs in sources:
        if os.path.exists(path):
            if path.endswith('.xlsx'):
                df = pd.read_excel(path, **kwargs)
            else:
                df = pd.read_csv(path, **kwargs)
            
            for col in sym_cols:
                if col in df.columns:
                    symbols.update(df[col].dropna().astype(str).unique())
            for col in ent_cols:
                if col in df.columns:
                    entrez_ids.update(df[col].dropna().astype(str).unique())
            for col in ens_cols:
                if col in df.columns:
                    ensembl_ids.update(df[col].dropna().astype(str).unique())

    print(f"Collected {len(symbols)} symbols, {len(entrez_ids)} Entrez IDs, and {len(ensembl_ids)} Ensembl IDs.")

    mg = mygene.MyGeneInfo()
    all_queries = list(symbols) + list(entrez_ids) + list(ensembl_ids)
    all_queries = list(set([q for q in all_queries if q and q.lower() != 'nan']))
    
    print(f"Total unique queries for mygene (including aliases): {len(all_queries)}")
    
    results = mg.querymany(all_queries, 
                           scopes='symbol,entrezgene,ensembl.gene,alias',
                           fields='symbol,entrezgene,ensembl.gene,uniprot',
                           species='human',
                           as_dataframe=False)

    mapping = {}
    mapped_data = []
    for r in results:
        if 'notfound' in r:
            continue
            
        query = r.get('query')
        symbol = r.get('symbol')
        entrez = r.get('entrezgene')
        
        ensembl_val = None
        ensembl = r.get('ensembl')
        if isinstance(ensembl, list):
            ensembl_val = ensembl[0].get('gene')
        elif isinstance(ensembl, dict):
            ensembl_val = ensembl.get('gene')

        uniprot_id = None
        uniprot_info = r.get('uniprot', {})
        if isinstance(uniprot_info, dict):
            uniprot_id = uniprot_info.get('Swiss-Prot') or uniprot_info.get('TrEMBL')
            if isinstance(uniprot_id, list): uniprot_id = uniprot_id[0]
        elif isinstance(uniprot_info, list):
            uniprot_id = uniprot_info[0]

        if symbol:
            info = {'HGNC': symbol, 'ensemblID': ensembl_val, 'entrezID': entrez, 'UniprotID': uniprot_id}
            mapping[query] = info
            mapped_data.append({'original_symbol': query, **info})

    df_map = pd.DataFrame(mapped_data).drop_duplicates(subset=['original_symbol']).sort_values('HGNC')
    df_map.to_csv('data/HuRI_BioPlex_id_map.csv', index=False)
    print(f"Step 2: Updated data/HuRI_BioPlex_id_map.csv with {len(df_map)} entries.")

    def get_info(s, key):
        if pd.isna(s): return None
        return mapping.get(str(s), {}).get(key, None)

    print("Step 3: Creating standardized and enriched datasets...")

    # Define standardization tasks
    tasks = [
        {
            'src': 'data/huri_ppi.csv', 
            'out': 'data/huri_ppi.csv', 
            'from': 'from', 'to': 'to', 
            'orig_from': 'original_from', 'orig_to': 'original_to'
        },
        {
            'src': 'data/bioplex_293.tsv', 
            'out': 'data/bioplex_293.tsv', 
            'from': 'SymbolA', 'to': 'SymbolB', 
            'orig_from': 'original_SymbolA', 'orig_to': 'original_SymbolB',
            'sep': '\t'
        },
        {
            'src': 'data/bioplex_hct116.tsv', 
            'out': 'data/bioplex_hct116.tsv', 
            'from': 'SymbolA', 'to': 'SymbolB', 
            'orig_from': 'original_SymbolA', 'orig_to': 'original_SymbolB',
            'sep': '\t'
        },
        {
            'src': 'data/v2_edge.xlsx', 
            'out': 'data/v2_edge.xlsx', 
            'from': 'viral_protein', 'to': 'human_protein_HGNC', 
            'orig_from': 'viral_protein', 'orig_to': 'human_protein_HGNC'
        },
        {
            'src': 'data/HuSCI_PPIs.xlsx', 
            'out': 'data/HuSCI_PPIs.xlsx', 
            'from': 'Viral protein', 'to': 'Host protein', 
            'orig_from': 'Viral protein', 'orig_to': 'Host protein'
        },
        {
            'src': 'data/Supplementary Data 11.xlsx', 
            'out': 'data/bacterial_ppi.xlsx', 
            'from': 'Effector Abbreviation', 'to': 'Human protein symbol', 
            'orig_from': 'Effector Abbreviation', 'orig_to': 'Human protein symbol',
            'kwargs': {'sheet_name': '11A', 'header': 3}
        }
    ]

    for task in tasks:
        if not os.path.exists(task['src']):
            continue
            
        print(f"Processing {task['src']}...")
        if task['src'].endswith('.xlsx'):
            df = pd.read_excel(task['src'], **task.get('kwargs', {}))
        else:
            df = pd.read_csv(task['src'], sep=task.get('sep', ','))
            
        updated = df.copy()
        
        # Determine mapping keys
        # If 'from'/'to' don't exist yet (first time), use the task-defined source columns
        src_f = task['from'] if task['from'] in df.columns else task['orig_from']
        src_t = task['to'] if task['to'] in df.columns else task['orig_to']
        
        updated['from'] = df[src_f].map(lambda x: get_info(x, 'HGNC') or x)
        updated['to'] = df[src_t].map(lambda x: get_info(x, 'HGNC') or x)
        updated['original_from'] = df[task['orig_from']]
        updated['original_to'] = df[task['orig_to']]
        
        # Enrich with IDs
        updated['from_entrez'] = df[src_f].map(lambda x: get_info(x, 'entrezID'))
        updated['to_entrez'] = df[src_t].map(lambda x: get_info(x, 'entrezID'))
        updated['from_ensembl'] = df[src_f].map(lambda x: get_info(x, 'ensemblID'))
        updated['to_ensembl'] = df[src_t].map(lambda x: get_info(x, 'ensemblID'))
        updated['from_uniprot'] = df[src_f].map(lambda x: get_info(x, 'UniprotID'))
        updated['to_uniprot'] = df[src_t].map(lambda x: get_info(x, 'UniprotID'))
        
        # Standard column order
        std_cols = ['from', 'to', 'original_from', 'original_to', 
                    'from_entrez', 'to_entrez', 'from_ensembl', 'to_ensembl', 
                    'from_uniprot', 'to_uniprot']
        
        cols = std_cols + [c for c in updated.columns if c not in std_cols]
        
        # Save output (overwriting original OR using new standardized name)
        if task['out'].endswith('.xlsx'):
            updated[cols].to_excel(task['out'], index=False)
        else:
            sep = task.get('sep', ',')
            updated[cols].to_csv(task['out'], index=False, sep=sep)
        
        print(f"Done: {task['out']}")

    # Clean up old _updated files if they exist to avoid confusion
    for p in ['data/v2_edge_updated.xlsx', 'data/HuSCI_PPIs_updated.xlsx', 'data/Supplementary_Data_11_updated.xlsx']:
        if os.path.exists(p):
            os.remove(p)
            print(f"Removed redundant file: {p}")

if __name__ == "__main__":
    main()
