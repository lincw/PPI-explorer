from shiny import ui, render
from config import DATASET_ABBR, DATASET_FULL, DATASET_COLORS, STATS

def overview_server(input, output, session):
    @output
    @render.ui
    def welcome_stats():
        stats_list = []
        meta_info = {
            "mygene": {
                "text": "Updated: ",
                "date": "2026-03-12CET"
                },
            "huri": {
                "text": "Ref: ",
                "link_text": "Luck et al, Nature 2020",
                "link": "https://doi.org/10.1038/s41586-020-2188-x"
            },
            "bioplex_293": {
                "text": "Ref: ",
                "link_text": "Huttlin et al, Cell 2021",
                "link": "https://doi.org/10.1016/j.cell.2021.04.011"
            },
            "bioplex_hct116": {
                "text": "Ref: ",
                "link_text": "Huttlin et al, Cell 2021",
                "link": "https://doi.org/10.1016/j.cell.2021.04.011"
            },
            "pancov": {
                "text": "Ref: ",
                "link_text": "",
                "link": "#"
            },
            "husci": {
                "text": "Ref: ",
                "link_text": "Kim et al, Nat Biot 2022",
                "link": "https://doi.org/10.1038/s41587-022-01475-z"
            },
            "bacterial": {
                "text": "Ref: ",
                "link_text": "Young et al, Nat Micro",
                "link": "https://doi.org/10.1038/s41564-025-02241-y"
            },
            "intact": {
                "text": "Ref: ",
                "link_text": "Orchard et al, Nucleic Acids Res 2014",
                "link": "https://doi.org/10.1093/nar/gkt1166",
                "desc": [
                    "High-confidence human-human physical interactions parsed from the IntAct database (2026-02-17).",
                    "The interactome was filtered based on the following criteria:",
                    "• Participants: Only interactions where both participants are human proteins (PSI-MI: MI:0326).",
                    "• Interaction Types: Restricted to physical interactions, specifically colocalization (MI:0407), physical association (MI:0914), and direct interaction (MI:0915).",
                    "• Confidence: Every interaction is supported by at least one published study and one experimental detection method."
                ]
            }
        }
        
        # Separate list for data descriptions (non-PPI datasets like mygene)
        description_list = []
        
        def format_desc(desc):
            if not desc: return ""
            if isinstance(desc, list):
                # Standard color and size for clarity as requested
                return ui.div(*[ui.p(p, style="margin-bottom: 8px;") for p in desc])
            return ui.p(desc, style="margin-bottom: 8px;")

        # Display mygene/nomenclature info separately at the top
        if "mygene" in meta_info:
            info = meta_info["mygene"]
            label = DATASET_FULL.get("mygene", "Human gene nomenclature (MyGene.info)")
            description_list.append(ui.div(
                ui.h5(label, style="color: #8e44ad; font-weight: 700;"),
                ui.p(ui.em(info["text"]), info.get("date", ""), style="color: #666;"),
                ui.tags.details(
                    ui.tags.summary("View Annotation", style="cursor: pointer; color: #8e44ad; font-weight: 600; margin-bottom: 10px;"),
                    ui.div(format_desc(info.get("desc")), style="padding: 10px; border-top: 1px solid #eee; margin-top: 5px;")
                ) if info.get("desc") else "",
                style="margin-bottom: 25px; border-left: 5px solid #8e44ad; padding: 15px; background-color: #fdfaff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);"
            ))

        for name, s in STATS.items():
            if name == "mygene": continue
            info = meta_info.get(name, {"text": ""})
            label = DATASET_ABBR.get(name, name.upper())
            full_label = DATASET_FULL.get(name, label)
            color = DATASET_COLORS.get(name, "#3498db")
            
            # Build the main list items (prominent)
            list_items = []
            if info.get("text"):
                list_items.append(ui.tags.li(
                    ui.strong("Reference: "),
                    ui.tags.a(info["link_text"], href=info["link"], target="_blank", 
                              style=f"color: {color}; text-decoration: none; font-weight: 500;")
                ))
            
            list_items.append(ui.tags.li(ui.strong("Total Interactions: "), f"{s['num_interactions']:,}"))
            list_items.append(ui.tags.li(ui.strong("Unique Proteins: "), f"{s['num_genes']:,}"))
            list_items.append(ui.tags.li(ui.strong("Top Hub: "), ui.span(s['top_hub'], style=f"color: {color}; font-weight: 600;")))

            stats_list.append(ui.card(
                ui.card_header(
                    ui.div(
                        ui.span(label, style=f"color: {color}; font-weight: 700; font-size: 1.1em;"),
                        style="display: flex; align-items: center;"
                    )
                ),
                ui.div(
                    ui.tags.p(full_label, style="font-size: 0.9em; color: #7f8c8d; margin-bottom: 15px; border-bottom: 1px solid #f8f9fa; padding-bottom: 8px;"),
                    ui.tags.ul(
                        *list_items,
                        style="list-style-type: none; padding-left: 0; margin-bottom: 15px;"
                    ),
                    ui.tags.details(
                        ui.tags.summary("Click for Annotation", style=f"cursor: pointer; color: {color}; font-weight: 600; outline: none;"),
                        ui.div(
                            format_desc(info.get("desc")),
                            style="margin-top: 12px; padding: 12px; background-color: #f9f9f9; border-radius: 4px; border-left: 3px solid #eee;"
                        )
                    ) if info.get("desc") else "",
                    style="padding: 5px;"
                ),
                style=f"border-top: 5px solid {color}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%;"
            ))
            
        return ui.div(
            ui.div(*(description_list), style="margin-bottom: 25px;"),
            ui.layout_columns(
                *stats_list,
                col_widths=4 # Every card is exactly 1/3 of the row width
            )
        )
