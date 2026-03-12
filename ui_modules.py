from shiny import ui
from config import CSS_FILE

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.markdown("### Global Search"),
        ui.input_select(
            "dataset", 
            "Select PPI Dataset:", 
            choices={
                "huri": "HuRI PPI",
                "bioplex_293": "BioPlex HEK 293T",
                "bioplex_hct116": "BioPlex HCT116"
            },
            selected="huri"
        ),
        ui.input_text("query_gene", "Gene Symbol:", placeholder="e.g., CALM2"),
        ui.input_action_button("submit", "Start New Search", class_="btn-primary w-100"),
        ui.input_action_button("reset", "Reset to Home", class_="btn-outline-secondary w-100 mt-2"),
        ui.hr(),
        ui.markdown("""
        #### How to Interact:
        1. **Search** for a protein.
        2. **Double-click** a node to:
           - **Focus:** New search from here.
           - **Expand:** Add neighbors to graph.
           - **Delete:** Remove node.
        """)
    ),
    ui.navset_card_pill(
        ui.nav_panel(
            "Overview",
            ui.card(
                ui.markdown("Search for a protein on the left to explore its interaction network.")
            ),
            ui.card(
                ui.card_header("Dataset Summary Statistics"),
                ui.output_ui("welcome_stats")
            )
        ),
        ui.nav_panel(
            "Subnetwork",
            ui.output_ui("subnetwork_stats_ui"),
            ui.card(
                ui.card_header("Interactive Visualization (Double-click node to interact)"),
                ui.output_ui("graph_container"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Interaction Table"),
                ui.div(
                    ui.div(
                        ui.input_text("filter_text", "Filter current table:", placeholder="Type to filter..."),
                        style="width: 300px; margin-bottom: 0;"
                    ),
                    ui.div(
                        ui.input_action_button("filter_submit", "Apply Filter", class_="btn-primary", style="height: 38px;"),
                        style="margin-left: 10px; align-self: flex-end; margin-bottom: 16px;"
                    ),
                    style="display: flex; align-items: flex-end; justify-content: flex-start;"
                ),
                ui.div(
                    ui.download_button("download_edges", "Download Edges (CSV)", class_="btn-outline-primary btn-sm me-2"),
                    ui.download_button("download_nodes", "Download Nodes (CSV)", class_="btn-outline-secondary btn-sm me-2"),
                    style="margin: 8px 0;"
                ),
                ui.output_ui("interaction_table_ui")
            )
        ),
        ui.nav_panel(
            "Multi-gene query",
            ui.card(
                ui.card_header("Multi-gene query"),
                ui.layout_columns(
                    ui.input_select(
                        "genelist_dataset",
                        "Dataset:",
                        choices={
                            "huri": "HuRI PPI",
                            "bioplex_293": "BioPlex HEK 293T",
                            "bioplex_hct116": "BioPlex HCT116"
                        },
                        selected="huri"
                    ),
                    ui.input_text_area(
                        "genelist_input",
                        "Gene Symbols (one per line or comma-separated):",
                        placeholder="e.g.\nCALM2\nTP53\nBRCA1",
                        rows=6
                    ),
                    col_widths=[3, 9]
                ),
                ui.input_action_button("genelist_submit", "Find Connections", class_="btn-primary"),
            ),
            ui.output_ui("genelist_stats_ui"),
            ui.card(
                ui.card_header("Connection Graph (red = connected, grey = isolated)"),
                ui.output_ui("genelist_graph_container"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Connection Table"),
                ui.output_ui("genelist_table_ui")
            )
        ),
        ui.nav_panel(
            "Settings",
            ui.card(
                ui.card_header("Cache Management"),
                ui.output_text("cache_info"),
                ui.input_action_button("clear_cache", "Clear Temporary Graph Files", class_="btn-danger")
            )
        ),
        id="main_tabs"
    ),
    ui.include_css(CSS_FILE),
    ui.tags.script("""
        window.addEventListener("message", function(event) {
            if (event.data && event.data.type === "node_clicked") {
                Shiny.setInputValue("clicked_node", event.data.nodeId, {priority: "event"});
            }
        });
    """),
    title="PPI Subnetwork Explorer"
)
