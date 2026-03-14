from shiny import ui

def subnetwork_ui():
    return ui.nav_panel(
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
    )
