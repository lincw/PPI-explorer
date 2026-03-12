# PPI Shiny App

An interactive Protein-Protein Interaction (PPI) visualization tool built with [Shiny for Python](https://shiny.posit.co/py/). This application allows users to explore interaction networks from high-quality datasets like BioPlex and HuRI.

## Features

- **Interactive Network Visualization:** Uses `vis-network` for high-performance graph rendering.
- **Multiple Datasets:** Supports BioPlex 293, BioPlex HCT116, and HuRI.
- **Gene-Centric Exploration:** Search for specific genes and visualize their first-degree interaction partners.
- **REST API Endpoint:** Programmatic access to generate subnetwork HTML fragments.
- **Dockerized Deployment:** Ready for production with Docker and Uvicorn.

## Project Structure

```text
├── app.py                # Main Shiny application & Starlette API
├── config.py             # Global configurations and data initialization
├── data_loader.py        # Logic for reading PPI datasets and neighbor retrieval
├── graph_utils.py        # NetworkX and Pyvis graph generation utilities
├── ui_modules.py         # Modular UI component definitions
├── server_modules.py     # Server-side reactive logic
├── update_data.py        # Script for data maintenance
├── generate_static_graph.py # CLI tool for static graph generation
├── Dockerfile            # Container configuration
├── deploy.sh             # Deployment automation script
├── data/                 # PPI dataset storage (TSV/CSV)
├── lib/                  # Local JS/CSS dependencies (vis-network, tom-select)
└── www/                  # Static assets and generated graph cache
```

## Installation

### Using Conda (Recommended)

As per the project guidelines, use `conda` to manage the environment and packages:

```bash
# Create and activate the environment
conda create -n bio_env python=3.12
conda activate bio_env

# Install dependencies from conda-forge
conda install -c conda-forge shiny pandas networkx pyvis uvicorn
```

### Local Development

Run the application locally using `shiny`:

```bash
shiny run app.py --reload
```

Or via `uvicorn` (as configured in the Dockerfile):

```bash
uvicorn app:app --host 0.0.0.0 --port 5070
```

## Deployment with Docker

The project includes a `Dockerfile` and `deploy.sh` for easy deployment.

```bash
chmod +x deploy.sh
./deploy.sh
```

The application will be accessible at `http://localhost:5070/ppi`.

## API Usage

The application exposes a subnetwork generation endpoint:

`GET /graph/{dataset}/{gene}`

Example: `http://localhost:5070/ppi/graph/huri/TP53`

## License

This project is licensed under the [MIT License](LICENSE).
