from shiny import ui

def settings_ui():
    return ui.nav_panel(
        "Settings",
        ui.card(
            ui.card_header("Cache Management"),
            ui.output_text("cache_info"),
            ui.input_action_button("clear_cache", "Clear Temporary Graph Files", class_="btn-danger")
        )
    )
