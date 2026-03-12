import pandas as pd
import mygene
import os

def update_ppi_data():
    mg = mygene.MyGeneInfo()
    
    # Load datasets
    print("Loading datasets...")
    huri = pd.read_csv("data/huri_ppi.csv")
    bp293 = pd.read_csv("data/bioplex_293.tsv", sep='\t')
    bphct = pd.read_csv("data/bioplex_hct116.tsv", sep='\t')
    
    # Extract all unique symbols to map
    all_symbols = set()
    if 'original_from' in huri.columns:
        all_symbols.update(huri['original_from'].unique())
        all_symbols.update(huri['original_to'].unique())
    else:
        all_symbols.update(huri['from'].unique())
        all_symbols.update(huri['to'].unique())
        
    if 'original_SymbolA' in bp293.columns:
        all_symbols.update(bp293['original_SymbolA'].unique())
        all_symbols.update(bp293['original_SymbolB'].unique())
    else:
        all_symbols.update(bp293['SymbolA'].unique())
        all_symbols.update(bp293['SymbolB'].unique())

    if 'original_SymbolA' in bphct.columns:
        all_symbols.update(bphct['original_SymbolA'].unique())
        all_symbols.update(bphct['original_SymbolB'].unique())
    else:
        all_symbols.update(bphct['SymbolA'].unique())
        all_symbols.update(bphct['SymbolB'].unique())
    
    symbols_list = [str(s) for s in all_symbols if pd.notna(s)]
    print(f"Found {len(symbols_list)} unique symbols. Querying mygene (the gold rule)...")
    
    # Query mygene for latest HGNC symbols and other IDs
    # We prioritize standard uniprot fields, then uniprot_kb, then others
    results = mg.querymany(symbols_list, scopes='symbol,alias', 
                           fields='symbol,ensembl.gene,uniprot,uniprot_kb,accession.protein', 
                           species='human')
    
    mapping = {}
    for res in results:
        query = res['query']
        if 'symbol' in res:
            latest = res['symbol']
            ensembl = ""
            if 'ensembl' in res:
                if isinstance(res['ensembl'], list):
                    ensembl = res['ensembl'][0]['gene']
                else:
                    ensembl = res['ensembl']['gene']
            
            uniprot = ""
            # Priority: Swiss-Prot > TrEMBL > uniprot_kb > accession.protein
            # We must be careful because 'uniprot' in results can be a dict with Swiss-Prot/TrEMBL
            if 'uniprot' in res:
                u_dict = res['uniprot']
                if 'Swiss-Prot' in u_dict:
                    val = u_dict['Swiss-Prot']
                    uniprot = val[0] if isinstance(val, list) else val
                elif 'TrEMBL' in u_dict:
                    val = u_dict['TrEMBL']
                    uniprot = val[0] if isinstance(val, list) else val
            
            if not uniprot and 'uniprot_kb' in res:
                # uniprot_kb can contain GenBank IDs sometimes, we prefer 6-character ones if possible
                val = res['uniprot_kb']
                if isinstance(val, list):
                    # Try to find a real UniProt ID (usually 6 or 10 chars, not starting with A if it's GenBank-like)
                    # Actually, Swiss-Prot/TrEMBL above should catch most.
                    uniprot = val[0]
                else:
                    uniprot = val
                
            if not uniprot and 'accession' in res and 'protein' in res['accession']:
                val = res['accession']['protein']
                uniprot_raw = val[0] if isinstance(val, list) else val
                if uniprot_raw: 
                    uniprot = uniprot_raw.split('.')[0]

            mapping[query] = {
                'latest_symbol': latest,
                'ensembl': ensembl,
                'uniprot': uniprot
            }
        else:
            mapping[query] = {
                'latest_symbol': query,
                'ensembl': "",
                'uniprot': ""
            }

    # 1) Create new id_map
    print("Creating updated ID map...")
    map_data = []
    for orig, info in mapping.items():
        map_data.append({
            'original_symbol': orig,
            'HGNC': info['latest_symbol'],
            'ensemblID': info['ensembl'],
            'UniprotID': info['uniprot']
        })
    
    new_map_df = pd.DataFrame(map_data)
    new_map_df.to_csv("data/HuRI_BioPlex_id_map_updated.csv", index=False)
    
    # 2) Create updated PPI datasets
    print("Updating PPI datasets...")
    
    def get_latest(sym):
        return mapping.get(str(sym), {}).get('latest_symbol', sym)

    def get_orig_cols(df, col_a, col_b):
        orig_a = f'original_{col_a}'
        orig_b = f'original_{col_b}'
        if orig_a in df.columns and orig_b in df.columns:
            return df[orig_a], df[orig_b]
        return df[col_a], df[col_b]

    # Update HuRI
    orig_f, orig_t = get_orig_cols(huri, 'from', 'to')
    huri_updated = pd.DataFrame({
        'from': orig_f.map(get_latest),
        'to': orig_t.map(get_latest),
        'original_from': orig_f,
        'original_to': orig_t
    })
    huri_updated.to_csv("data/huri_ppi_updated.csv", index=False)
    
    # Update BioPlex 293
    orig_sa, orig_sb = get_orig_cols(bp293, 'SymbolA', 'SymbolB')
    bp293_updated = bp293.copy()
    if 'original_SymbolA' not in bp293_updated.columns:
        bp293_updated['original_SymbolA'] = orig_sa
        bp293_updated['original_SymbolB'] = orig_sb
    bp293_updated['SymbolA'] = orig_sa.map(get_latest)
    bp293_updated['SymbolB'] = orig_sb.map(get_latest)
    bp293_updated.to_csv("data/bioplex_293_updated.tsv", sep='\t', index=False)
    
    # Update BioPlex HCT116
    orig_sa, orig_sb = get_orig_cols(bphct, 'SymbolA', 'SymbolB')
    bphct_updated = bphct.copy()
    if 'original_SymbolA' not in bphct_updated.columns:
        bphct_updated['original_SymbolA'] = orig_sa
        bphct_updated['original_SymbolB'] = orig_sb
    bphct_updated['SymbolA'] = orig_sa.map(get_latest)
    bphct_updated['SymbolB'] = orig_sb.map(get_latest)
    bphct_updated.to_csv("data/bioplex_hct116_updated.tsv", sep='\t', index=False)
    
    print("Done!")

if __name__ == "__main__":
    update_ppi_data()
