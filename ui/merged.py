from shiny import ui

def merged_ui():
    return ui.nav_panel(
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
    )
