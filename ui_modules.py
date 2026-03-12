from shiny import ui
from config import CSS_FILE, DATASET_ABBR

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.div(
            ui.markdown("#### Global Database Search"),
            ui.input_text("global_query", None, placeholder="e.g., N"),
            ui.input_action_button("global_submit", "Search Everywhere", class_="btn-info btn-sm w-100"),
            style="margin-bottom: 10px;"
        ),
        ui.hr(style="margin: 10px 0;"),
        ui.div(
            ui.markdown("#### Subnetwork Search"),
            ui.input_select(
                "dataset", 
                "Select Dataset:", 
                choices=DATASET_ABBR,
                selected="huri"
            ),
            ui.input_text("query_gene", "Gene Symbol:", placeholder="e.g., CALM2"),
            ui.div(
                ui.input_action_button("submit", "Search", class_="btn-primary btn-sm w-100"),
                ui.input_action_button("reset", "Reset", class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ),
            style="margin-bottom: 10px;"
        ),
        ui.hr(style="margin: 10px 0;"),
        ui.tags.small(
            ui.markdown("""
**How to Interact:**
1. **Search** for a protein.
2. **Double-click** a node to:
   - **Focus / Expand / Delete**
""")
        )
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
            "Global Results",
            ui.card(
                ui.card_header("Search Results Across All Datasets"),
                ui.output_ui("global_search_results_ui"),
                ui.div(ui.input_action_button("hidden_jump_btn", "hidden"), style="display:none;")
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
                    ui.tags.label("Filter current table:", class_="mb-0 me-2", style="white-space: nowrap; font-weight: 500;"),
                    ui.input_text("filter_text", None, placeholder="Type to filter..."),
                    ui.input_action_button("filter_submit", "Apply Filter", class_="btn-primary ms-2"),
                    class_="d-flex align-items-center mb-4 inline-filter"
                ),
                ui.output_ui("interaction_table_ui")
            )
        ),
        ui.nav_panel(
            "Merged Network",
            ui.card(
                ui.card_header("Global Network Search (Across all datasets)"),
                ui.layout_columns(
                    ui.input_text_area(
                        "merged_query",
                        "Gene Symbol(s):",
                        placeholder="Single: CALM2\nMultiple: TP53, BRCA1, BRCA2",
                        rows=4
                    ),
                    ui.div(
                        ui.input_action_button("merged_submit", "Search Global Network", class_="btn-primary w-100"),
                        ui.HTML("""
<div class="mt-2 text-muted" style="font-size: 0.85em;">
    <ul class="mb-0 ps-3">
        <li><strong>Single gene:</strong> Shows all direct neighbors across all databases.</li>
        <li><strong>Multiple genes:</strong> Shows connections <em>among</em> input genes across all databases.</li>
    </ul>
</div>
"""),
                    ),
                    col_widths=[8, 4],
                    align="end"
                )
            ),
            ui.output_ui("merged_stats_ui"),
            ui.card(
                ui.card_header("Global Interactive Visualization (Edges colored by source)"),
                ui.output_ui("merged_graph_container"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Global Interaction Table"),
                ui.output_ui("merged_table_ui")
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
                        choices=DATASET_ABBR,
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
