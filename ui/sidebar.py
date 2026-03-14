from shiny import ui
from config import DATASET_ABBR

def sidebar_ui():
    return ui.sidebar(
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
    )
