from shiny import ui, render, reactive, Session
import os
import uuid
from config import STATIC_DIR

# Import sub-modules
from server.overview import overview_server
from server.global_search import global_search_server
from server.subnetwork import subnetwork_server
from server.merged import merged_server
from server.genelist import genelist_server

def server(input, output, session: Session):
    session_id = str(uuid.uuid4())[:8]
    
    # Shared reactive values
    root_genes = reactive.Value(set())
    deleted_nodes = reactive.Value(set())
    pending_gene = reactive.Value("")
    global_search_results = reactive.Value([])

    # Initialize sub-modules
    overview_server(input, output, session)
    global_search_server(input, output, session, global_search_results, root_genes, deleted_nodes)
    subnetwork_server(input, output, session, session_id, root_genes, deleted_nodes, pending_gene)
    merged_server(input, output, session, session_id)
    genelist_server(input, output, session, session_id)

    @output
    @render.text
    def cache_info():
        # Trigger on clear_cache but also every time tab is viewed
        input.clear_cache() 
        files = list(STATIC_DIR.glob("ppi_subnetwork_*.html")) + \
                list(STATIC_DIR.glob("ppi_merged_*.html")) + \
                list(STATIC_DIR.glob("ppi_genelist_*.html"))
        count = len(files)
        size = sum(f.stat().st_size for f in files) / (1024 * 1024)
        return f"Current Cache: {count} temporary files ({size:.2f} MB)"

    @reactive.Effect
    @reactive.event(input.clear_cache)
    def handle_clear_cache():
        for p in STATIC_DIR.glob("ppi_subnetwork_*.html"):
            try: p.unlink()
            except: pass
        for p in STATIC_DIR.glob("ppi_merged_*.html"):
            try: p.unlink()
            except: pass
        for p in STATIC_DIR.glob("ppi_genelist_*.html"):
            try: p.unlink()
            except: pass
        ui.notification_show("Cache cleared.", type="message")
