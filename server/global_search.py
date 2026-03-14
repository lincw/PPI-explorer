from shiny import ui, render, reactive
from config import GLOBAL_DATA, DATASET_ABBR

def global_search_server(input, output, session, global_search_results, root_genes, deleted_nodes):
    @reactive.Effect
    @reactive.event(input.global_submit)
    def handle_global_submit():
        query = input.global_query().strip().upper()
        if not query:
            return
        
        results = []
        for key, df in GLOBAL_DATA.items():
            mask = (df['from'].str.upper() == query) | (df['to'].str.upper() == query)
            if 'original_from' in df.columns:
                mask |= (df['original_from'].str.upper() == query)
            if 'original_to' in df.columns:
                mask |= (df['original_to'].str.upper() == query)
            
            sub_df = df[mask]
            if not sub_df.empty:
                results.append({
                    "key": key,
                    "label": DATASET_ABBR.get(key, key.replace("_", " ").upper()),
                    "interactions": len(sub_df)
                })
        
        global_search_results.set(results)
        ui.update_navset("main_tabs", selected="Global Results")

    @output
    @render.ui
    def global_search_results_ui():
        results = global_search_results()
        query = input.global_query().strip().upper()
        
        if not results:
            if query:
                return ui.div(f"No interactions found for '{query}' in any dataset.", class_="alert alert-warning")
            return ui.div("Enter a gene symbol in the sidebar and click 'Search Everywhere'.", class_="text-muted")
        
        rows = []
        for res in results:
            onclick = f"Shiny.setInputValue('jump_dataset', '{res['key']}'); Shiny.setInputValue('jump_gene', '{query}'); document.getElementById('hidden_jump_btn').click();"
            rows.append(ui.tags.tr(
                ui.tags.td(res['label']),
                ui.tags.td(str(res['interactions'])),
                ui.tags.td(
                    ui.tags.button("View Network", class_="btn btn-sm btn-outline-primary", onclick=onclick)
                )
            ))

        return ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th("Dataset"),
                    ui.tags.th("Interactions with " + query),
                    ui.tags.th("Action")
                )
            ),
            ui.tags.tbody(*rows),
            class_="table table-hover"
        )

    @reactive.Effect
    @reactive.event(input.hidden_jump_btn)
    def handle_jump():
        dataset = input.jump_dataset()
        gene = input.jump_gene()
        if dataset and gene:
            ui.update_select("dataset", selected=dataset)
            ui.update_text("query_gene", value=gene)
            root_genes.set({gene})
            deleted_nodes.set(set())
            ui.update_navset("main_tabs", selected="Subnetwork")
            ui.update_text("filter_text", value="")
