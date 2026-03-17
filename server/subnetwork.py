from shiny import ui, render, reactive
import pandas as pd
import os
import shutil
import data_loader
import graph_utils
from config import GLOBAL_DATA, DATASET_ABBR, DIRECTED_DATASETS, STATIC_DIR

def subnetwork_server(input, output, session, session_id, root_genes, deleted_nodes, pending_gene):
    
    @reactive.Effect
    @reactive.event(input.submit)
    def handle_submit():
        gene = input.query_gene().strip().upper()
        if gene:
            root_genes.set({gene})
            deleted_nodes.set(set())
            ui.update_text("filter_text", value="")
            ui.update_navset("main_tabs", selected="Subnetwork")

    @reactive.Effect
    @reactive.event(input.reset)
    def handle_reset():
        root_genes.set(set())
        deleted_nodes.set(set())
        ui.update_text("query_gene", value="")
        ui.update_text("filter_text", value="")

    @reactive.Effect
    @reactive.event(input.clicked_node)
    def handle_node_click():
        gene = input.clicked_node()
        if gene:
            pending_gene.set(gene)
            m = ui.modal(
                ui.p(f"What would you like to do with {gene}?"),
                title="Node Interaction",
                footer=ui.div(
                    ui.input_action_button("btn_focus", "Focus on this Node", class_="btn-primary"),
                    ui.input_action_button("btn_expand", "Expand Subnetwork", class_="btn-success"),
                    ui.input_action_button("btn_delete", "Remove from View", class_="btn-danger"),
                    ui.modal_button("Cancel"),
                    style="display: flex; gap: 5px; justify-content: flex-end;"
                ),
                easy_close=True
            )
            ui.modal_show(m)

    @reactive.Effect
    @reactive.event(input.btn_focus)
    def handle_focus():
        gene = pending_gene()
        root_genes.set({gene})
        deleted_nodes.set(set())
        ui.update_text("query_gene", value=gene)
        ui.modal_remove()
        ui.update_text("filter_text", value="")

    @reactive.Effect
    @reactive.event(input.btn_expand)
    def handle_expand():
        gene = pending_gene()
        current_roots = root_genes.get()
        if gene not in current_roots:
            root_genes.set(current_roots | {gene})
        current_deleted = deleted_nodes.get()
        if gene in current_deleted:
            deleted_nodes.set(current_deleted - {gene})
        ui.modal_remove()
        ui.update_text("filter_text", value="")

    @reactive.Effect
    @reactive.event(input.btn_delete)
    def handle_delete():
        gene = pending_gene()
        current_deleted = deleted_nodes.get()
        deleted_nodes.set(current_deleted | {gene})
        current_roots = root_genes.get()
        if gene in current_roots:
            root_genes.set(current_roots - {gene})
        ui.modal_remove()
        ui.notification_show(f"Node {gene} removed from view.", duration=3)

    @reactive.Calc
    def subnetwork_data_full():
        roots = root_genes()
        deleted = deleted_nodes()
        if not roots: return None
        df = GLOBAL_DATA.get(input.dataset())
        if df is None: return None
        
        # Get the full subnetwork (roots, neighbors, and all links among them)
        final_df = data_loader.get_subnetwork(df, roots)
        
        if not final_df.empty and deleted:
            deleted_upper = {str(d).strip().upper() for d in deleted}
            mask = ~final_df['from'].str.upper().isin(deleted_upper) & ~final_df['to'].str.upper().isin(deleted_upper)
            final_df = final_df[mask]
            
        return final_df

    @output
    @render.ui
    def subnetwork_stats_ui():
        df = subnetwork_data_full()
        if df is None or df.empty: return ui.div()
        nodes = pd.concat([df['from'], df['to']]).nunique()
        edges = len(df)
        roots_count = len(root_genes())
        label = DATASET_ABBR.get(input.dataset(), input.dataset().upper())
        return ui.card(
            ui.div(
                ui.div(ui.strong("Dataset: "), label, style="margin-right: 20px;"),
                ui.div(ui.strong("Root Genes: "), f"{roots_count}", style="margin-right: 20px;"),
                ui.div(ui.strong("Total Nodes: "), f"{nodes}", style="margin-right: 20px;"),
                ui.div(ui.strong("Total Edges: "), f"{edges}"),
                style="display: flex; flex-direction: row; justify-content: start; align-items: center; padding: 5px 15px;"
            ),
            style="margin-bottom: 10px; border-left: 5px solid #009879;"
        )

    applied_filter = reactive.Value("")

    @reactive.Effect
    @reactive.event(input.filter_submit, ignore_none=False)
    def handle_filter_submit():
        applied_filter.set(input.filter_text().strip().upper())

    @reactive.Calc
    def filtered_data():
        df = subnetwork_data_full()
        if df is None or df.empty: return df
        filter_val = applied_filter()
        if not filter_val: return df
        mask = df.apply(lambda row: row.astype(str).str.upper().str.contains(filter_val).any(), axis=1)
        return df[mask]

    @output
    @render.ui
    def graph_container():
        df = subnetwork_data_full()
        if df is None: return ui.div("Search for a gene to begin.", class_="text-muted")
        if df.empty: return ui.div("No interactions to display.", class_="alert alert-warning")
        
        filter_val = applied_filter()
        filtered_df = filtered_data()
        
        # Only treat as "filtered" if the user has actually submitted a non-empty string
        active_filtered_df = filtered_df if filter_val else None
        
        roots = root_genes()
        # Include applied filter in slug to differentiate cached files
        slug = f"{input.dataset()}_{str(hash(tuple(sorted(list(roots)))))[:10]}_{str(hash(filter_val))[:6]}"
        is_directed = input.dataset() in DIRECTED_DATASETS
        graph_file_path = graph_utils.create_subnetwork_graph(df, roots, height="600px", filtered_df=active_filtered_df, directed=is_directed)
        
        if graph_file_path and os.path.exists(graph_file_path):
            unique_filename = f"ppi_subnetwork_{session_id}_{slug}.html"
            dest_path = STATIC_DIR / unique_filename
            shutil.copy(graph_file_path, dest_path)
            return ui.tags.iframe(src=f"static/{unique_filename}", width="100%", height="600px", style="border:none;")
        return ui.div("Error generating graph.", class_="alert alert-danger")

    @output
    @render.ui
    def interaction_table_ui():
        df = filtered_data()
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
        
        def highlight_diff(orig, curr):
            if pd.isna(orig) or str(orig).strip() == "": return "-"
            if str(orig).upper() != str(curr).upper():
                return f'<span class="diff-symbol" title="Original: {orig}, Current: {curr}">{orig}</span>'
            return orig

        # Detect non-human proteins (no Ensembl mapping) before columns are transformed
        from_is_human = display_df['from_ensembl'].notna() if 'from_ensembl' in display_df.columns else pd.Series(True, index=display_df.index)
        to_is_human = display_df['to_ensembl'].notna() if 'to_ensembl' in display_df.columns else pd.Series(True, index=display_df.index)

        for col in ['from_ensembl', 'to_ensembl']:
            display_df[col] = display_df[col].apply(make_ensembl_link)
        for col in ['from_uniprot', 'to_uniprot']:
            display_df[col] = display_df[col].apply(make_uniprot_link)
        for col in ['from_entrez', 'to_entrez']:
            display_df[col] = display_df[col].apply(make_entrez_link)

        if 'original_from' in display_df.columns:
            display_df['original_from'] = display_df.apply(lambda x: highlight_diff(x['original_from'], x['from']), axis=1)
        if 'original_to' in display_df.columns:
            display_df['original_to'] = display_df.apply(lambda x: highlight_diff(x['original_to'], x['to']), axis=1)

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
                ui.download_button("download_edges", "Download Edges (CSV)", class_="btn-outline-primary btn-sm me-2"),
                ui.download_button("download_nodes", "Download Nodes (CSV)", class_="btn-outline-secondary btn-sm me-2"),
                style="margin: 8px 0;"
            ),
            ui.div(ui.HTML(html_table), class_="table-container")
        )

    @render.download(filename=lambda: f"subnetwork_edges_{'-'.join(root_genes())}.csv")
    def download_edges():
        df = filtered_data()
        if df is not None:
            yield df.to_csv(index=False)

    @render.download(filename=lambda: f"subnetwork_nodes_{'-'.join(root_genes())}.csv")
    def download_nodes():
        df = filtered_data()
        if df is not None:
            all_nodes = pd.concat([df['from'], df['to']]).drop_duplicates().reset_index(drop=True)
            all_nodes.name = 'symbol'
            yield all_nodes.to_csv(index=False)
