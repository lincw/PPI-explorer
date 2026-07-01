from shiny import ui

def custom_network_ui():
    return ui.nav_panel(
        "Custom Network",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_text_area(
                    "custom_interaction_list", 
                    "Paste Interaction Pairs:", 
                    placeholder="GeneA,GeneB\nGeneC GeneD\nGeneE\tGeneF",
                    rows=10
                ),
                ui.input_action_button("custom_submit", "Generate Network", class_="btn-primary w-100"),
                ui.hr(),
                ui.markdown("""
                **Instructions:**
                - Enter one pair per line.
                - Separators: comma, space, or tab.
                - **Direction (Optional):** Add a 3rd column:
                  - `1`: Directed (A → B)
                  - `-1`: Directed (B → A)
                  - No value or other: Undirected
                - Examples:
                  - `TP53,MDM2` (Undirected)
                  - `BRCA1 BRCA2 1` (Directed BRCA1 → BRCA2)
                  - `EGFR\tSTAT3\t-1` (Directed STAT3 → EGFR)
                """)
            ),
            ui.card(
                ui.card_header("Custom Network Visualization"),
                ui.output_ui("custom_graph_container"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Interaction Table"),
                ui.output_ui("custom_interaction_table_ui")
            )
        )
    )
