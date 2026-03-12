import networkx as nx
from pyvis.network import Network
import tempfile
import os
from config import DATASET_COLORS

def create_merged_graph(edge_df, root_genes, height="600px"):
    """
    Creates a pyvis graph for the merged dataset.
    edge_df: DataFrame with 'from', 'to', and 'dataset' columns.
    root_genes: list of input genes to highlight.
    """
    if edge_df is None or edge_df.empty:
        return None

    net = Network(height=height, width="100%", notebook=False, directed=False)
    
    # Track nodes
    nodes = set(edge_df['from'].str.upper()) | set(edge_df['to'].str.upper())
    root_genes = {str(g).strip().upper() for g in root_genes}
    
    # Add nodes
    for node in nodes:
        is_root = node in root_genes
        color = "#e74c3c" if is_root else "#3498db"
        size = 30 if is_root else 20
        net.add_node(node, label=node, color=color, size=size, font={'size': 18},
                     title=node)
    
    # Add edges with colors from config
    for _, row in edge_df.iterrows():
        u, v = str(row['from']).upper(), str(row['to']).upper()
        ds = row.get('dataset', 'unknown')
        color = DATASET_COLORS.get(ds, "#bdc3c7")
        net.add_edge(u, v, color=color, width=2, title=f"Dataset: {ds}")

    # Use same options and injection as other graphs
    options = """
    var options = {
      "nodes": { "font": { "size": 18 }, "borderWidth": 2 },
      "edges": { "smooth": false },
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -50, "centralGravity": 0.01, "springLength": 100, "springConstant": 0.08, "avoidOverlap": 1 },
        "solver": "forceAtlas2Based",
        "stabilization": { "enabled": true, "iterations": 200 }
      },
      "interaction": { "hover": true, "navigationButtons": false }
    }
    """
    net.set_options(options)

    tmp_dir = tempfile.gettempdir()
    tmp_file = os.path.join(tmp_dir, f"ppi_merged_{os.getpid()}.html")
    net.save_graph(tmp_file)

    with open(tmp_file, "r") as f:
        html = f.read()

    # Reuse the same injection script for consistency
    injection = """
    <style>
        .export-controls { position: absolute; top: 10px; right: 10px; z-index: 1000; display: flex; gap: 5px; }
        .export-btn { padding: 5px 10px; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; font-family: sans-serif; font-size: 12px; }
    </small>
    <div class="export-controls">
        <button class="export-btn" onclick="downloadPNG()">PNG</button>
    </div>
    <script type="text/javascript">
    function downloadPNG() {
        var canvas = document.getElementsByTagName('canvas')[0];
        if (!canvas) return;
        var link = document.createElement('a');
        link.download = 'ppi_merged_graph.png';
        link.href = canvas.toDataURL("image/png");
        link.click();
    }
    (function() {
        var checkNetwork = setInterval(function() {
            if (typeof network !== 'undefined') {
                clearInterval(checkNetwork);
                network.on("stabilizationIterationsDone", function () { network.fit(); });
                setTimeout(function() { network.fit(); }, 500);
            }
        }, 100);
    })();
    </script>
    """
    new_html = html.replace("</body>", injection + "</body>")
    with open(tmp_file, "w") as f:
        f.write(new_html)
    return tmp_file

def create_gene_list_graph(df, gene_list):
    """
    Creates a pyvis graph showing ONLY connections among the given gene_list.
    """
    gene_set = {str(g).strip().upper() for g in gene_list if str(g).strip()}
    if not gene_set:
        return None

    # Filter edges: BOTH endpoints must be in gene_set
    mask_from = df['from'].str.upper().isin(gene_set)
    if 'original_from' in df.columns:
        mask_from |= df['original_from'].str.upper().isin(gene_set)
        
    mask_to = df['to'].str.upper().isin(gene_set)
    if 'original_to' in df.columns:
        mask_to |= df['original_to'].str.upper().isin(gene_set)
        
    edge_df = df[mask_from & mask_to]

    net = Network(height="600px", width="100%", notebook=False, directed=False)
    options = """
    var options = {
      "nodes": {
        "font": { "size": 18 },
        "borderWidth": 2
      },
      "edges": {
        "color": { "inherit": true },
        "smooth": false
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08,
          "avoidOverlap": 1
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "enabled": true,
          "iterations": 200,
          "updateInterval": 25
        }
      },
      "interaction": {
        "navigationButtons": true,
        "hover": true,
        "hideEdgesOnDrag": true
      }
    }
    """
    net.set_options(options)

    # In strict mode, only input genes are shown
    connected = set()
    if not edge_df.empty:
        connected = (set(edge_df['from'].str.upper()) | set(edge_df['to'].str.upper())) & gene_set

    for gene in gene_set:
        color = "#e74c3c" if gene in connected else "#95a5a6"
        size = 25 if gene in connected else 18
        net.add_node(gene, label=gene, color=color, size=size, font={'size': 18},
                     title=gene)

    for _, row in edge_df.iterrows():
        net.add_edge(str(row['from']).upper(), str(row['to']).upper())

    tmp_dir = tempfile.gettempdir()
    tmp_file = os.path.join(tmp_dir, "ppi_genelist_temp.html")
    net.save_graph(tmp_file)

    with open(tmp_file, "r") as f:
        html_content = f.read()

    # Add export controls and styling
    injection = """
    <style>
        .export-controls {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            display: flex;
            gap: 5px;
        }
        .export-btn {
            padding: 5px 10px;
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            font-family: sans-serif;
            font-size: 12px;
        }
        .export-btn:hover { background-color: #e2e6ea; }
    </style>
    <div class="export-controls">
        <button class="export-btn" onclick="downloadPNG()">PNG</button>
        <button class="export-btn" onclick="downloadPDF()">PDF</button>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script type="text/javascript">
    function downloadPNG() {
        var canvas = document.getElementsByTagName('canvas')[0];
        if (!canvas) return;
        var link = document.createElement('a');
        link.download = 'ppi_graph.png';
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    async function downloadPDF() {
        const { jsPDF } = window.jspdf;
        var positions = network.getPositions();
        var nodeIds = Object.keys(positions);
        if (nodeIds.length === 0) return;

        var xs = nodeIds.map(id => positions[id].x);
        var ys = nodeIds.map(id => positions[id].y);
        var minX = Math.min(...xs), maxX = Math.max(...xs);
        var minY = Math.min(...ys), maxY = Math.max(...ys);
        var pad = 80;
        var w = Math.max((maxX - minX) + pad * 2, 200);
        var h = Math.max((maxY - minY) + pad * 2, 200);

        var pdf = new jsPDF({
            orientation: w > h ? 'l' : 'p',
            unit: 'pt',
            format: [w, h]
        });

        // Edges
        var edgesData = network.body.data.edges.get();
        pdf.setDrawColor(189, 195, 199);
        pdf.setLineWidth(1.2);
        edgesData.forEach(function(edge) {
            var from = positions[edge.from], to = positions[edge.to];
            if (from && to) {
                pdf.line(from.x - minX + pad, from.y - minY + pad,
                         to.x - minX + pad, to.y - minY + pad);
            }
        });

        // Nodes
        var nodesData = network.body.data.nodes.get();
        var nodeMap = {};
        nodesData.forEach(function(n) { nodeMap[n.id] = n; });

        nodeIds.forEach(function(id) {
            var px = positions[id].x - minX + pad;
            var py = positions[id].y - minY + pad;
            var node = nodeMap[id] || {};
            var color = node.color || '#3498db';
            if (typeof color === 'object') color = color.background || '#3498db';
            var r = parseInt(color.slice(1,3), 16);
            var g = parseInt(color.slice(3,5), 16);
            var b = parseInt(color.slice(5,7), 16);
            var radius = (node.size || 20) * 0.8;

            pdf.setFillColor(r, g, b);
            pdf.setDrawColor(r * 0.7, g * 0.7, b * 0.7);
            pdf.setLineWidth(0.8);
            pdf.circle(px, py, radius, 'FD');

            pdf.setFontSize(10);
            pdf.setTextColor(30, 30, 30);
            pdf.text(node.label || id, px, py - radius - 4, { align: 'center' });
        });

        pdf.save("ppi_graph.pdf");
    }
    </script>
    """
    new_html = html_content.replace("</body>", injection + "</body>")

    with open(tmp_file, "w") as f:
        f.write(new_html)

    return tmp_file


def create_subnetwork_graph(sub_df, root_genes, height="100%", filtered_df=None):
    """
    Creates a pyvis interactive network from the subnetwork DataFrame.
    root_genes: a list or set of genes to highlight as roots.
    filtered_df: if provided, edges in this df will be highlighted.
    """
    if sub_df.empty:
        return None
        
    G = nx.Graph()
    if isinstance(root_genes, str):
        root_genes = {root_genes.strip().upper()}
    else:
        root_genes = {str(g).strip().upper() for g in root_genes}
    
    # Track nodes for color coding
    nodes = set()
    
    for _, row in sub_df.iterrows():
        g1, g2 = str(row['from']).strip().upper(), str(row['to']).strip().upper()
        nodes.add(g1)
        nodes.add(g2)
        G.add_edge(g1, g2)

    # Highlighted edges and nodes from filtered_df
    highlighted_edges = set()
    highlighted_nodes = set()
    if filtered_df is not None and not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            u, v = str(row['from']).strip().upper(), str(row['to']).strip().upper()
            highlighted_edges.add(tuple(sorted((u, v))))
            highlighted_nodes.add(u)
            highlighted_nodes.add(v)
    
    # Initialize Pyvis Network with CDN resources
    net = Network(height=height, width="100%", notebook=False, directed=False)
    
    # Advanced options for performance and stability
    options = """
    var options = {
      "nodes": {
        "font": { "size": 18 },
        "borderWidth": 2
      },
      "edges": {
        "color": { "inherit": true },
        "smooth": false,
        "width": 1.2
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08,
          "avoidOverlap": 1
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "enabled": true,
          "iterations": 200,
          "updateInterval": 25
        }
      },
      "interaction": {
        "navigationButtons": false,
        "hover": true,
        "hideEdgesOnDrag": true,
        "hideNodesOnDrag": false
      }
    }
    """
    net.set_options(options)
    
    # Add nodes with specific styling
    for node in nodes:
        is_root = node in root_genes
        is_highlighted = node in highlighted_nodes
        
        if is_root:
            color = "#e74c3c" # Red for roots
        elif is_highlighted:
            color = "#f39c12" # Orange for highlighted (matches filter)
        else:
            color = "#3498db" # Blue for others
            
        size = 30 if is_root else (25 if is_highlighted else 20)
        border_width = 4 if is_highlighted else 2
        
        net.add_node(node, label=node, color=color, size=size, font={'size': 18}, 
                     borderWidth=border_width,
                     title=f"Double-click to {'expand' if is_root else 'focus/expand'} {node}")
        
    # Add edges
    for u, v in G.edges():
        is_highlighted = tuple(sorted((u, v))) in highlighted_edges
        color = "#e67e22" if is_highlighted else "#bdc3c7"
        width = 4 if is_highlighted else 1.2
        net.add_edge(u, v, color=color, width=width)

    # Store in a temporary HTML file
    tmp_dir = tempfile.gettempdir()
    # Use a generic name since the actual unique filename is handled in app.py
    tmp_file = os.path.join(tmp_dir, "ppi_subnetwork_temp.html")
    net.save_graph(tmp_file)

    # Read the file and inject the script before </body>
    with open(tmp_file, "r") as f:
        html_content = f.read()

    # The custom script to handle double-clicks, auto-fit, PNG and PDF export
    injection = """
    <style>
        .export-controls {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            display: flex;
            gap: 5px;
        }
        .export-btn {
            padding: 5px 10px;
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            font-family: sans-serif;
            font-size: 12px;
        }
        .export-btn:hover { background-color: #e2e6ea; }
    </style>
    <div class="export-controls">
        <button class="export-btn" onclick="downloadPNG()">PNG</button>
        <button class="export-btn" onclick="downloadPDF()">PDF</button>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script type="text/javascript">
    function downloadPNG() {
        var canvas = document.getElementsByTagName('canvas')[0];
        if (!canvas) return;
        var link = document.createElement('a');
        link.download = 'ppi_network.png';
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    async function downloadPDF() {
        const { jsPDF } = window.jspdf;
        var positions = network.getPositions();
        var nodeIds = Object.keys(positions);
        if (nodeIds.length === 0) return;

        var xs = nodeIds.map(id => positions[id].x);
        var ys = nodeIds.map(id => positions[id].y);
        var minX = Math.min(...xs), maxX = Math.max(...xs);
        var minY = Math.min(...ys), maxY = Math.max(...ys);
        var pad = 80;
        var w = Math.max((maxX - minX) + pad * 2, 200);
        var h = Math.max((maxY - minY) + pad * 2, 200);

        var pdf = new jsPDF({
            orientation: w > h ? 'l' : 'p',
            unit: 'pt',
            format: [w, h]
        });

        // Edges
        var edgesData = network.body.data.edges.get();
        pdf.setDrawColor(189, 195, 199);
        pdf.setLineWidth(1.2);
        edgesData.forEach(function(edge) {
            var from = positions[edge.from], to = positions[edge.to];
            if (from && to) {
                pdf.line(from.x - minX + pad, from.y - minY + pad,
                         to.x - minX + pad, to.y - minY + pad);
            }
        });

        // Nodes
        var nodesData = network.body.data.nodes.get();
        var nodeMap = {};
        nodesData.forEach(function(n) { nodeMap[n.id] = n; });

        nodeIds.forEach(function(id) {
            var px = positions[id].x - minX + pad;
            var py = positions[id].y - minY + pad;
            var node = nodeMap[id] || {};
            var color = node.color || '#3498db';
            if (typeof color === 'object') color = color.background || '#3498db';
            var r = parseInt(color.slice(1,3), 16);
            var g = parseInt(color.slice(3,5), 16);
            var b = parseInt(color.slice(5,7), 16);
            var radius = (node.size || 20) * 0.8;

            pdf.setFillColor(r, g, b);
            pdf.setDrawColor(r * 0.7, g * 0.7, b * 0.7);
            pdf.setLineWidth(0.8);
            pdf.circle(px, py, radius, 'FD');

            pdf.setFontSize(10);
            pdf.setTextColor(30, 30, 30);
            pdf.text(node.label || id, px, py - radius - 4, { align: 'center' });
        });

        pdf.save("ppi_network.pdf");
    }

    (function() {
        var checkNetwork = setInterval(function() {
            if (typeof network !== 'undefined') {
                clearInterval(checkNetwork);
                
                // Auto-fit the network once stabilized
                network.on("stabilizationIterationsDone", function () {
                    network.fit();
                });
                
                // Also fit after a short delay just in case
                setTimeout(function() { network.fit(); }, 500);

                network.on("doubleClick", function (params) {
                    if (params.nodes.length > 0) {
                        var nodeId = params.nodes[0];
                        // Notify parent window (Shiny)
                        if (window.parent) {
                            window.parent.postMessage({
                                type: "node_clicked",
                                nodeId: nodeId
                            }, "*");
                        }
                    }
                });
            }
        }, 100);
    })();
    </script>
    """
    
    # Inject before </body>
    new_html = html_content.replace("</body>", injection + "</body>")
    
    with open(tmp_file, "w") as f:
        f.write(new_html)
    
    return tmp_file
