from shiny import ui, render, reactive, Session
import pandas as pd
import os
import urllib.parse
import uuid
import shutil
import data_loader
import graph_utils
from config import STATIC_DIR, GLOBAL_DATA, DATASETS, STATS

def server(input, output, session: Session):
    session_id = str(uuid.uuid4())[:8]
    root_genes = reactive.Value(set())
    deleted_nodes = reactive.Value(set())
    pending_gene = reactive.Value("")

    @reactive.Effect
    def handle_url_params():
        search = session.input[".clientdata_url_search"]()
        if not search:
            return

        params = urllib.parse.parse_qs(search.lstrip("?"))
        gene_param = params.get("gene") or params.get("query_gene")
        dataset_param = params.get("dataset")

        if dataset_param and dataset_param[0] in DATASETS:
            ui.update_select("dataset", selected=dataset_param[0])
        
        if gene_param:
            gene = gene_param[0].strip().upper()
            ui.update_text("query_gene", value=gene)
            root_genes.set({gene})
            deleted_nodes.set(set())
            ui.update_navset("main_tabs", selected="Subnetwork")
            ui.update_text("filter_text", value="")

    @reactive.Effect
    @reactive.event(input.submit)
    def handle_submit():
        gene = input.query_gene().strip().upper()
        if gene:
            root_genes.set({gene})
            deleted_nodes.set(set())
            ui.update_navset("main_tabs", selected="Subnetwork")
            ui.update_text("filter_text", value="")

    @reactive.Effect
    @reactive.event(input.reset)
    def handle_reset():
        root_genes.set(set())
        deleted_nodes.set(set())
        ui.update_text("query_gene", value="")
        ui.update_navset("main_tabs", selected="Overview")

    @reactive.Effect
    @reactive.event(input.clicked_node)
    def handle_node_click():
        new_gene = input.clicked_node().strip().upper()
        if new_gene:
            pending_gene.set(new_gene)
            m = ui.modal(
                ui.markdown(f"**How would you like to interact with {new_gene}?**"),
                title="Node Interaction",
                footer=ui.div(
                    ui.input_action_button("btn_focus", "Focus", class_="btn-primary"),
                    ui.input_action_button("btn_expand", "Expand", class_="btn-success"),
                    ui.input_action_button("btn_delete", "Delete Node", class_="btn-danger"),
                    ui.modal_button("Cancel"),
                    class_="d-flex gap-2 justify-content-end"
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

    @output
    @render.text
    def cache_info():
        input.clear_cache()
        files = list(STATIC_DIR.glob("ppi_subnetwork_*.html"))
        count = len(files)
        size = sum(f.stat().st_size for f in files) / (1024 * 1024)
        return f"Current Cache: {count} temporary files ({size:.2f} MB)"

    @reactive.Effect
    @reactive.event(input.clear_cache)
    def handle_clear_cache():
        for p in STATIC_DIR.glob("ppi_subnetwork_*.html"):
            try: p.unlink()
            except: pass
        ui.notification_show("Cache cleared.", type="message")

    @output
    @render.ui
    def welcome_stats():
        stats_list = []
        meta_info = {
            "huri": {
                "label": "HuRI PPI",
                "text": "Ref: ",
                "link_text": "Luck et al Nature 2020",
                "link": "https://doi.org/10.1038/s41586-020-2188-x"
            },
            "bioplex_293": {
                "label": "BioPlex HEK 293T",
                "text": "Ref: ",
                "link_text": "Huttlin et al Cell 2021",
                "link": "https://doi.org/10.1016/j.cell.2021.04.011"
            },
            "bioplex_hct116": {
                "label": "BioPlex HCT116",
                "text": "Ref: ",
                "link_text": "Huttlin et al Cell 2021",
                "link": "https://doi.org/10.1016/j.cell.2021.04.011"
            }
        }
        
        for name, s in STATS.items():
            info = meta_info.get(name, {"label": name.replace("_", " ").upper(), "text": ""})
            metadata = ""
            if info.get("text"):
                metadata = ui.p(
                    ui.em(info["text"]),
                    ui.tags.a(info["link_text"], href=info["link"], target="_blank") if "link" in info else "",
                    style="font-size: 0.85em; color: #666;"
                )
            
            stats_list.append(ui.div(
                ui.h5(info["label"]),
                metadata,
                ui.tags.ul(
                    ui.tags.li(f"Total Interactions: {s['num_interactions']:,}"),
                    ui.tags.li(f"Total Unique Proteins: {s['num_genes']:,}"),
                    ui.tags.li(f"Top Hub: {s['top_hub']} ({s['max_degree']} connections)"),
                ),
                style="margin-bottom: 15px; border-left: 4px solid #3498db; padding-left: 15px;"
            ))
        return ui.div(*stats_list)

    @reactive.Calc
    def subnetwork_data_full():
        roots = root_genes()
        deleted = deleted_nodes()
        if not roots: return None
        df = GLOBAL_DATA.get(input.dataset())
        if df is None: return None
        all_results = [data_loader.get_neighbors(df, r) for r in roots]
        combined = pd.concat(all_results).drop_duplicates()
        if deleted:
            combined = combined[~combined['from'].isin(deleted) & ~combined['to'].isin(deleted)]
        return combined

    @output
    @render.ui
    def subnetwork_stats_ui():
        df = subnetwork_data_full()
        if df is None or df.empty: return ui.div()
        nodes = pd.concat([df['from'], df['to']]).nunique()
        edges = len(df)
        roots_count = len(root_genes())
        return ui.card(
            ui.div(
                ui.div(ui.strong("Dataset: "), input.dataset().upper(), style="margin-right: 20px;"),
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
        graph_file_path = graph_utils.create_subnetwork_graph(df, roots, height="600px", filtered_df=active_filtered_df)
        
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
        
        def make_hgnc_link(symbol):
            if pd.isna(symbol) or str(symbol).strip() == "": return "-"
            # Note: HGNC usually expects #!/symbol/ for symbols, but as requested using #!/hgnc_id/
            return f'<a href="https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/{symbol}" target="_blank">{symbol}</a>'
        
        def highlight_diff(orig, curr):
            if pd.isna(orig) or str(orig).strip() == "": return "-"
            if str(orig).upper() != str(curr).upper():
                return f'<span class="diff-symbol" title="Original: {orig}, Current: {curr}">{orig}</span>'
            return orig

        for col in ['from_ensembl', 'to_ensembl']:
            display_df[col] = display_df[col].apply(make_ensembl_link)
        for col in ['from_uniprot', 'to_uniprot']:
            display_df[col] = display_df[col].apply(make_uniprot_link)
        
        if 'original_from' in display_df.columns:
            display_df['original_from'] = display_df.apply(lambda x: highlight_diff(x['original_from'], x['from']), axis=1)
        if 'original_to' in display_df.columns:
            display_df['original_to'] = display_df.apply(lambda x: highlight_diff(x['original_to'], x['to']), axis=1)

        for col in ['from', 'to']:
            display_df[col] = display_df[col].apply(make_hgnc_link)

        # Create MultiIndex for clearer grouping
        final_cols = []
        col_tuples = []
        
        # Partner A group
        final_cols.append('from')
        col_tuples.append(('Partner A', 'Symbol'))
        if 'original_from' in display_df.columns:
            final_cols.append('original_from')
            col_tuples.append(('Partner A', 'Original'))
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
        final_cols.append('to_ensembl')
        col_tuples.append(('Partner B', 'Ensembl'))
        final_cols.append('to_uniprot')
        col_tuples.append(('Partner B', 'UniProt'))

        display_df = display_df[final_cols]
        display_df.columns = pd.MultiIndex.from_tuples(col_tuples)
        
        html_table = display_df.to_html(classes="interaction-table", escape=False, index=False)
        return ui.div(ui.HTML(html_table), class_="table-container")

    @render.download(filename=lambda: f"edges_{input.dataset()}_{'-'.join(sorted(root_genes()))}.csv")
    def download_edges():
        df = subnetwork_data_full()
        if df is None or df.empty:
            yield ""
            return
        out = df[['from', 'to']].copy()
        out.columns = ['Symbol A', 'Symbol B']
        yield out.to_csv(index=False)

    @render.download(filename=lambda: f"nodes_{input.dataset()}_{'-'.join(sorted(root_genes()))}.csv")
    def download_nodes():
        df = subnetwork_data_full()
        if df is None or df.empty:
            yield ""
            return
        all_nodes = pd.concat([df['from'], df['to']]).drop_duplicates().reset_index(drop=True)
        all_nodes.name = 'symbol'
        roots = root_genes()
        nodes_df = pd.DataFrame({'symbol': all_nodes})
        nodes_df['is_root'] = nodes_df['symbol'].isin(roots)
        yield nodes_df.to_csv(index=False)


    genelist_genes = reactive.Value([])

    @reactive.Effect
    @reactive.event(input.genelist_submit)
    def handle_genelist_submit():
        raw = input.genelist_input()
        import re
        genes = [g.strip().upper() for g in re.split(r"[\n,]+", raw) if g.strip()]
        genelist_genes.set(genes)

    @reactive.Calc
    def genelist_edge_data():
        genes = genelist_genes()
        if not genes: return None
        df = GLOBAL_DATA.get(input.genelist_dataset())
        if df is None: return None
        gene_set = set(genes)
        
        # Match "from" side (current or original)
        mask_from = df['from'].str.upper().isin(gene_set)
        if 'original_from' in df.columns:
            mask_from |= df['original_from'].str.upper().isin(gene_set)
            
        # Match "to" side (current or original)
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
        n_input = len(genes)
        n_edges = len(edge_df) if edge_df is not None else 0
        connected = set()
        if edge_df is not None and not edge_df.empty:
            connected = set(edge_df['from'].str.upper()) | set(edge_df['to'].str.upper())
        n_isolated = n_input - len(connected)
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
        graph_file_path = graph_utils.create_gene_list_graph(df, genes)
        if graph_file_path and os.path.exists(graph_file_path):
            slug = f"genelist_{input.genelist_dataset()}_{hash(tuple(sorted(genes)))}"
            unique_filename = f"ppi_genelist_{session_id}_{slug}.html"
            dest_path = STATIC_DIR / unique_filename
            shutil.copy(graph_file_path, dest_path)
            return ui.tags.iframe(src=f"static/{unique_filename}", width="100%", height="600px", style="border:none;")
        return ui.div("Error generating graph.", class_="alert alert-danger")

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
        for col in ['from_ensembl', 'to_ensembl']:
            display_df[col] = display_df[col].apply(make_ensembl_link)
        for col in ['from_uniprot', 'to_uniprot']:
            display_df[col] = display_df[col].apply(make_uniprot_link)
        
        # Create MultiIndex for clearer grouping
        final_cols = []
        col_tuples = []
        
        # Partner A group
        final_cols.append('from')
        col_tuples.append(('Partner A', 'Symbol'))
        if 'original_from' in display_df.columns:
            final_cols.append('original_from')
            col_tuples.append(('Partner A', 'Original'))
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
        final_cols.append('to_ensembl')
        col_tuples.append(('Partner B', 'Ensembl'))
        final_cols.append('to_uniprot')
        col_tuples.append(('Partner B', 'UniProt'))

        display_df = display_df[final_cols]
        display_df.columns = pd.MultiIndex.from_tuples(col_tuples)
        
        html_table = display_df.to_html(classes="interaction-table", escape=False, index=False)
        return ui.div(ui.HTML(html_table), class_="table-container")
