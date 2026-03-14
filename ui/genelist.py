from shiny import ui
from config import DATASET_ABBR

def genelist_ui():
    return ui.nav_panel(
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
    )
