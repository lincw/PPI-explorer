from shiny import App
import os
from starlette.responses import HTMLResponse
from starlette.requests import Request

import config
import data_loader
import graph_utils
from ui_modules import app_ui
from server_modules import server

# Initialize workspace and load data
config.init_workspace()
config.cleanup_old_graphs()
config.load_global_data()

from starlette.applications import Starlette
from starlette.routing import Route

# --- Graph API Endpoint (Method 2) ---
async def graph_api_endpoint(request: Request):
    print(f"DEBUG: API request for dataset={request.path_params.get('dataset')}, gene={request.path_params.get('gene')}")
    dataset_key = request.path_params.get("dataset")
    gene_symbol = request.path_params.get("gene", "").upper()
    
    if dataset_key not in config.GLOBAL_DATA:
        return HTMLResponse(f"Dataset '{dataset_key}' not found. Available: {list(config.GLOBAL_DATA.keys())}", status_code=404)
        
    df = config.GLOBAL_DATA[dataset_key]
    sub_df = data_loader.get_subnetwork(df, [gene_symbol])
    
    if sub_df.empty:
        return HTMLResponse(f"No interactions found for {gene_symbol} in {dataset_key}", status_code=404)
        
    # Generate the graph HTML
    is_directed = dataset_key in config.DIRECTED_DATASETS
    tmp_file = graph_utils.create_subnetwork_graph(sub_df, {gene_symbol}, directed=is_directed)
    if not tmp_file or not os.path.exists(tmp_file):
        return HTMLResponse("Error generating graph", status_code=500)
        
    with open(tmp_file, "r") as f:
        html = f.read()
    
    # Clean up local dependencies for standalone view
    html = html.replace('<script src="lib/bindings/utils.js"></script>', "")
    
    # Remove margins/paddings and scrollbars for a "pure graph" look
    html = html.replace("<body>", '<body style="margin:0; padding:0; overflow:hidden;">')
    
    return HTMLResponse(content=html)

app = App(app_ui, server, static_assets={"/static": str(config.STATIC_DIR)})

# Insert route directly into the beginning of the Starlette router
app.starlette_app.router.routes.insert(0, Route("/graph/{dataset}/{gene}", graph_api_endpoint))
