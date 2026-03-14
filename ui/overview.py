from shiny import ui

def overview_ui():
    return ui.nav_panel(
        "Overview",
        ui.card(
            ui.card_header("Dataset Summary Statistics"),
            ui.output_ui("welcome_stats")
        )
    )
