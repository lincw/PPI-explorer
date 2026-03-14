from shiny import ui
from config import CSS_FILE

# Import sub-modules
from ui.sidebar import sidebar_ui
from ui.overview import overview_ui
from ui.global_results import global_results_ui
from ui.subnetwork import subnetwork_ui
from ui.merged import merged_ui
from ui.genelist import genelist_ui
from ui.settings import settings_ui

app_ui = ui.page_sidebar(
    sidebar_ui(),
    ui.navset_card_pill(
        overview_ui(),
        global_results_ui(),
        subnetwork_ui(),
        merged_ui(),
        genelist_ui(),
        settings_ui(),
        id="main_tabs"
    ),
    ui.include_css(CSS_FILE),
    ui.tags.head(
        ui.tags.link(rel="icon", href="data:,")
    ),
    # Floating Sticky Note HTML
    ui.div(
        ui.div(
            ui.div("Sticky Note", style="flex-grow: 1;"),
            ui.span("×", class_="sticky-note-close", onclick="document.getElementById('sticky-note-container').style.display='none';"),
            id="sticky-note-header"
        ),
        ui.tags.textarea(id="sticky-note-content", placeholder="Paste text here..."),
        id="sticky-note-container"
    ),
    ui.tags.script("""
        window.addEventListener("message", function(event) {
            if (event.data && event.data.type === "node_clicked") {
                Shiny.setInputValue("clicked_node", event.data.nodeId, {priority: "event"});
            }
        });
        
        // Draggable logic for Sticky Note
        (function() {
            var elmnt = document.getElementById("sticky-note-container");
            var header = document.getElementById("sticky-note-header");
            var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
            
            if (header) {
                header.onmousedown = dragMouseDown;
            } else {
                elmnt.onmousedown = dragMouseDown;
            }

            function dragMouseDown(e) {
                e = e || window.event;
                e.preventDefault();
                pos3 = e.clientX;
                pos4 = e.clientY;
                document.onmouseup = closeDragElement;
                document.onmousemove = elementDrag;
            }

            function elementDrag(e) {
                e = e || window.event;
                e.preventDefault();
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
                elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
                elmnt.style.bottom = 'auto'; // Disable bottom-anchoring once dragged
            }

            function closeDragElement() {
                document.onmouseup = null;
                document.onmousemove = null;
            }
        })();
    """),
    title="PPI Subnetwork Explorer"
)
