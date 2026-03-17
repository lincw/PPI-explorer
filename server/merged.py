from shiny import ui, render, reactive
import pandas as pd
import os
import shutil
import data_loader
import graph_utils
import re
from config import GLOBAL_DATA, STATIC_DIR

def merged_server(input, output, session, session_id):
    merged_genes = reactive.Value([])

    @reactive.Effect
    @reactive.event(input.merged_submit)
    def handle_merged_submit():
        raw = input.merged_query()
        raw_split = re.split(r"[\n,]+", raw)
        genes = []
        for g in raw_split:
            clean = g.strip().upper()
            if not clean: continue
            clean = re.sub(r"^[+\-*]\s*", "", clean)
            if clean: genes.append(clean)
        merged_genes.set(list(set(genes)))

    @reactive.Calc
    def merged_data_full():
        genes = merged_genes()
        if not genes: return None
        
        all_dfs = []
        for ds_key, df in GLOBAL_DATA.items():
            gene_set = set(genes)
            if len(genes) == 1:
                # Single protein: Show all neighbors and links among them
                sub_df = data_loader.get_subnetwork(df, genes).copy()
            else:
                # Multiple proteins: Show connections among them
                mask_from = df['from'].str.upper().isin(gene_set)
                if 'original_from' in df.columns: mask_from |= df['original_from'].str.upper().isin(gene_set)
                mask_to = df['to'].str.upper().isin(gene_set)
                if 'original_to' in df.columns: mask_to |= df['original_to'].str.upper().isin(gene_set)
                sub_df = df[mask_from & mask_to].copy()
            
            if not sub_df.empty:
                sub_df['dataset'] = ds_key
                all_dfs.append(sub_df)
        
        if not all_dfs: return pd.DataFrame()
        return pd.concat(all_dfs).drop_duplicates(subset=['from', 'to', 'dataset'])

    @output
    @render.ui
    def merged_stats_ui():
        df = merged_data_full()
        genes = merged_genes()
        if df is None or not genes: return ui.div()
        
        n_edges = len(df)
        n_nodes = pd.concat([df['from'], df['to']]).nunique()
        n_input = len(genes)
        
        return ui.card(
            ui.div(
                ui.div(ui.strong("Input Genes: "), f"{n_input}", style="margin-right: 20px;"),
                ui.div(ui.strong("Total Nodes: "), f"{n_nodes}", style="margin-right: 20px;"),
                ui.div(ui.strong("Total Edges: "), f"{n_edges}"),
                style="display: flex; flex-direction: row; justify-content: start; align-items: center; padding: 5px 15px;"
            ),
            style="margin-bottom: 10px; border-left: 5px solid #3498db;"
        )

    @output
    @render.ui
    def merged_graph_container():
        df = merged_data_full()
        genes = merged_genes()
        if df is None or not genes: return ui.div("Enter gene symbol(s) and click Search.", class_="text-muted")
        if df.empty: return ui.div("No interactions found among these genes.", class_="alert alert-warning")
        
        graph_file_path = graph_utils.create_merged_graph(df, genes)
        if graph_file_path and os.path.exists(graph_file_path):
            slug = f"merged_{hash(tuple(sorted(genes)))}"
            unique_filename = f"ppi_merged_{session_id}_{slug}.html"
            dest_path = STATIC_DIR / unique_filename
            shutil.copy(graph_file_path, dest_path)
            return ui.tags.iframe(src=f"static/{unique_filename}", width="100%", height="600px", style="border:none;")
        return ui.div("Error generating graph.", class_="alert alert-danger")

    @output
    @render.ui
    def merged_table_ui():
        df = merged_data_full()
        if df is None or df.empty: return ui.div()
        
        display_df = df.copy()
        def make_ensembl_link(eid):
            if pd.isna(eid) or str(eid).strip() == "": return "-"
            return f'<a href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={eid}" target="_blank">{eid}</a>'
        def make_uniprot_link(uid):
            if pd.isna(uid) or str(uid).strip() in ["-", ""]: return "-"
            return f'<a href="https://www.uniprot.org/uniprotkb/{uid}/entry" target="_blank">{uid}</a>'
        def make_entrez_link(eid):
            if pd.isna(eid) or str(eid).strip() == "": return "-"
            try:
                eid_clean = str(int(float(eid)))
            except:
                eid_clean = str(eid)
            return f'<a href="https://www.ncbi.nlm.nih.gov/gene/{eid_clean}" target="_blank">{eid_clean}</a>'
        def make_hgnc_link(symbol):
            if pd.isna(symbol) or str(symbol).strip() == "": return "-"
            return f'<a href="https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/{symbol}" target="_blank">{symbol}</a>'

        # Detect non-human proteins before columns are transformed
        from_is_human = display_df['from_ensembl'].notna() if 'from_ensembl' in display_df.columns else pd.Series(True, index=display_df.index)
        to_is_human = display_df['to_ensembl'].notna() if 'to_ensembl' in display_df.columns else pd.Series(True, index=display_df.index)

        for col in ['from_ensembl', 'to_ensembl']:
            display_df[col] = display_df[col].apply(make_ensembl_link)
        for col in ['from_uniprot', 'to_uniprot']:
            display_df[col] = display_df[col].apply(make_uniprot_link)
        for col in ['from_entrez', 'to_entrez']:
            display_df[col] = display_df[col].apply(make_entrez_link)

        # Only link to HGNC for human proteins; show plain text for viral/bacterial
        display_df.loc[from_is_human, 'from'] = display_df.loc[from_is_human, 'from'].apply(make_hgnc_link)
        display_df.loc[to_is_human, 'to'] = display_df.loc[to_is_human, 'to'].apply(make_hgnc_link)

        # Create MultiIndex for clearer grouping
        final_cols = []
        col_tuples = []

        # Partner A group
        final_cols.append('from')
        col_tuples.append(('Partner A', 'Symbol'))
        if 'original_from' in display_df.columns:
            final_cols.append('original_from')
            col_tuples.append(('Partner A', 'Original'))
        final_cols.append('from_entrez')
        col_tuples.append(('Partner A', 'Entrez'))
        final_cols.append('from_ensembl')
        col_tuples.append(('Partner A', 'Ensembl'))
        final_cols.append('from_uniprot')
        col_tuples.append(('Partner A', 'UniProt'))
        
        # Partner B group
        final_cols.append('to')
        col_tuples.append(('Partner B', 'Symbol'))
        if 'original_to' in display_df.columns:
            final_cols.append('original_to')
            col_tuples.append(('Partner B', 'Original'))
        final_cols.append('to_entrez')
        col_tuples.append(('Partner B', 'Entrez'))
        final_cols.append('to_ensembl')
        col_tuples.append(('Partner B', 'Ensembl'))
        final_cols.append('to_uniprot')
        col_tuples.append(('Partner B', 'UniProt'))

        # Add Dataset column
        final_cols.append('dataset')
        col_tuples.append(('Info', 'Dataset'))

        display_df = display_df[final_cols]
        display_df.columns = pd.MultiIndex.from_tuples(col_tuples)
            
        html_table = display_df.to_html(classes="interaction-table", escape=False, index=False)
        return ui.div(
            ui.div(
                ui.download_button("download_merged_edges", "Download Edges (CSV)", class_="btn-outline-primary btn-sm me-2"),
                ui.download_button("download_merged_nodes", "Download Nodes (CSV)", class_="btn-outline-secondary btn-sm me-2"),
                style="margin: 8px 0;"
            ),
            ui.div(ui.HTML(html_table), class_="table-container")
        )

    @render.download(filename=lambda: f"merged_edges_{len(merged_genes())}.csv")
    def download_merged_edges():
        df = merged_data_full()
        if df is not None:
            yield df.to_csv(index=False)

    @render.download(filename=lambda: f"merged_nodes_{len(merged_genes())}.csv")
    def download_merged_nodes():
        df = merged_data_full()
        if df is not None:
            all_nodes = pd.concat([df['from'], df['to']]).drop_duplicates().reset_index(drop=True)
            all_nodes.name = 'symbol'
            genes = merged_genes()
            nodes_df = pd.DataFrame({'symbol': all_nodes})
            nodes_df['is_input'] = nodes_df['symbol'].isin(genes)
            yield nodes_df.to_csv(index=False)
