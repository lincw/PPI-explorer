from shiny import ui, render, reactive
import pandas as pd
import os
import shutil
import data_loader
import graph_utils
import re
from config import GLOBAL_DATA, DIRECTED_DATASETS, STATIC_DIR

def genelist_server(input, output, session, session_id):
    genelist_genes = reactive.Value([])

    @reactive.Effect
    @reactive.event(input.genelist_submit)
    def handle_genelist_submit():
        raw = input.genelist_input()
        raw_split = re.split(r"[\n,]+", raw)
        genes = []
        for g in raw_split:
            clean = g.strip().upper()
            if not clean: continue
            clean = re.sub(r"^[+\-*]\s*", "", clean)
            if clean:
                genes.append(clean)
        genelist_genes.set(genes)

    @reactive.Calc
    def genelist_edge_data():
        genes = genelist_genes()
        if not genes: return None
        df = GLOBAL_DATA.get(input.genelist_dataset())
        if df is None: return None
        gene_set = set(genes)

        # Match interactions ONLY among the input genes (Strict Filtering)
        mask_from = df['from'].str.upper().isin(gene_set)
        if 'original_from' in df.columns:
            mask_from |= df['original_from'].str.upper().isin(gene_set)

        mask_to = df['to'].str.upper().isin(gene_set)
        if 'original_to' in df.columns:
            mask_to |= df['original_to'].str.upper().isin(gene_set)

        return df[mask_from & mask_to]

    @output
    @render.ui
    def genelist_stats_ui():
        genes = genelist_genes()
        if not genes: return ui.div()
        edge_df = genelist_edge_data()
        n_input = len(set(genes))
        n_edges = len(edge_df) if edge_df is not None else 0

        connected_in_input = set()
        if edge_df is not None and not edge_df.empty:
            connected_in_input = (set(edge_df['from'].str.upper()) | set(edge_df['to'].str.upper())) & set(genes)

        n_isolated = n_input - len(connected_in_input)
        return ui.card(
            ui.div(
                ui.div(ui.strong("Input Genes: "), str(n_input), style="margin-right: 20px;"),
                ui.div(ui.strong("Connections Found: "), str(n_edges), style="margin-right: 20px;"),
                ui.div(ui.strong("Isolated Genes: "), str(n_isolated)),
                style="display: flex; flex-direction: row; align-items: center; padding: 5px 15px;"
            ),
            style="margin-bottom: 10px; border-left: 5px solid #e67e22;"
        )

    @output
    @render.ui
    def genelist_graph_container():
        genes = genelist_genes()
        if not genes: return ui.div("Enter gene symbols and click 'Find Connections'.", class_="text-muted")
        df = GLOBAL_DATA.get(input.genelist_dataset())
        if df is None: return ui.div("Dataset not available.", class_="alert alert-warning")
        is_directed = input.genelist_dataset() in DIRECTED_DATASETS
        graph_file_path = graph_utils.create_gene_list_graph(df, genes, directed=is_directed)
        if graph_file_path and os.path.exists(graph_file_path):
            slug = f"genelist_{input.genelist_dataset()}_{hash(tuple(sorted(genes)))}"
            unique_filename = f"ppi_genelist_{session_id}_{slug}.html"
            dest_path = STATIC_DIR / unique_filename
            shutil.copy(graph_file_path, dest_path)
            return ui.tags.iframe(src=f"static/{unique_filename}", width="100%", height="600px", style="border:none;")
        return ui.div("Error generating graph.", class_="alert alert-danger")

    @render.download(filename=lambda: f"genelist_edges_{input.genelist_dataset()}_{len(genelist_genes())}.csv")
    def download_genelist_edges():
        df = genelist_edge_data()
        if df is not None:
            out = df[['from', 'to']].copy()
            out.columns = ['Symbol A', 'Symbol B']
            yield out.to_csv(index=False)

    @render.download(filename=lambda: f"genelist_nodes_{input.genelist_dataset()}_{len(genelist_genes())}.csv")
    def download_genelist_nodes():
        df = genelist_edge_data()
        if df is not None:
            all_nodes = pd.concat([df['from'], df['to']]).drop_duplicates().reset_index(drop=True)
            all_nodes.name = 'symbol'
            genes = genelist_genes()
            nodes_df = pd.DataFrame({'symbol': all_nodes})
            nodes_df['is_input'] = nodes_df['symbol'].isin(genes)
            yield nodes_df.to_csv(index=False)

    @output
    @render.ui
    def genelist_table_ui():
        edge_df = genelist_edge_data()
        if edge_df is None or edge_df.empty: return ui.div()
        display_df = edge_df.copy()
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

        if 'interaction' in display_df.columns:
            final_cols.append('interaction')
            col_tuples.append(('Info', 'Interaction'))

        display_df = display_df[final_cols]
        display_df.columns = pd.MultiIndex.from_tuples(col_tuples)

        html_table = display_df.to_html(classes="interaction-table", escape=False, index=False)
        return ui.div(
            ui.div(
                ui.download_button("download_genelist_edges", "Download Edges (CSV)", class_="btn-outline-primary btn-sm me-2"),
                ui.download_button("download_genelist_nodes", "Download Nodes (CSV)", class_="btn-outline-secondary btn-sm me-2"),
                style="margin: 8px 0;"
            ),
            ui.div(ui.HTML(html_table), class_="table-container")
        )
