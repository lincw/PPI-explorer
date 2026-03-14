from shiny import ui

def global_results_ui():
    return ui.nav_panel(
        "Global Results",
        ui.card(
            ui.card_header("Search Results Across All Datasets"),
            ui.output_ui("global_search_results_ui"),
            ui.div(ui.input_action_button("hidden_jump_btn", "hidden"), style="display:none;")
        )
    )
