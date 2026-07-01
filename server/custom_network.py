from shiny import ui, render, reactive
import pandas as pd
import os
import shutil
import re
import graph_utils
from config import STATIC_DIR

def custom_network_server(input, output, session, session_id):
    
    custom_data = reactive.Value(None)

    @reactive.Effect
    @reactive.event(input.custom_submit)
    def handle_custom_submit():
        raw_text = input.custom_interaction_list()
        if not raw_text.strip():
            ui.notification_show("Please enter at least one interaction pair.", type="warning")
            return
        
        lines = raw_text.strip().split('\n')
        pairs = []
        for line in lines:
            if not line.strip(): continue
            # Split by comma, tab, or one or more spaces
            parts = re.split(r'[,\t\s]+', line.strip())
            if len(parts) >= 2:
                u, v = parts[0].upper(), parts[1].upper()
                is_directed = False
                
                if len(parts) >= 3:
                    dir_val = str(parts[2]).strip()
                    if dir_val == "1":
                        is_directed = True
                        # from u to v (stay as is)
                    elif dir_val == "-1":
                        is_directed = True
                        # from v to u (swap)
                        u, v = v, u
                
                pairs.append({
                    'from': u, 
                    'to': v, 
                    'directed': is_directed
                })
            elif len(parts) == 1 and parts[0]:
                ui.notification_show(f"Skipping line '{line}': only one gene found.", type="warning")
        
        if not pairs:
            ui.notification_show("No valid interaction pairs found.", type="error")
            return
            
        df = pd.DataFrame(pairs)
        custom_data.set(df)

    @output
    @render.ui
    def custom_graph_container():
        df = custom_data()
        if df is None:
            return ui.div("Enter interaction pairs and click 'Generate Network' to begin.", class_="text-muted")
        
        # Use a generic slug for custom network
        slug = f"custom_{hash(input.custom_interaction_list()) % 10**8}"
        # We pass directed=False as global, but graph_utils will check row['directed']
        graph_file_path = graph_utils.create_subnetwork_graph(df, root_genes=[], height="600px")
        
        if graph_file_path and os.path.exists(graph_file_path):
            unique_filename = f"ppi_custom_{session_id}_{slug}.html"
            dest_path = STATIC_DIR / unique_filename
            shutil.copy(graph_file_path, dest_path)
            return ui.tags.iframe(src=f"static/{unique_filename}", width="100%", height="600px", style="border:none;")
        return ui.div("Error generating graph.", class_="alert alert-danger")

    @output
    @render.ui
    def custom_interaction_table_ui():
        df = custom_data()
        if df is None or df.empty:
            return ui.div()
            
        display_df = df.copy()
        # Make directed column more readable
        display_df['directed'] = display_df['directed'].apply(lambda x: "Directed (->)" if x else "Undirected")
        
        html_table = display_df.to_html(classes="interaction-table", escape=False, index=False)
        return ui.div(
            ui.div(
                ui.download_button("download_custom_edges", "Download Edges (CSV)", class_="btn-outline-primary btn-sm me-2"),
                style="margin: 8px 0;"
            ),
            ui.div(ui.HTML(html_table), class_="table-container")
        )

    @render.download(filename="custom_network_edges.csv")
    def download_custom_edges():
        df = custom_data()
        if df is not None:
            yield df.to_csv(index=False)
