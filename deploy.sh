#!/bin/bash

# Stop and remove existing container if it exists
docker stop ppi-explorer 2>/dev/null || true
docker rm ppi-explorer 2>/dev/null || true

# Build the image
docker build -t ppi-explorer .

# Run the container
# Mapping host 5070 to container 5070
# Only binding to localhost for Nginx to handle external access
docker run -d \
  --name ppi-explorer \
  --restart unless-stopped \
  -p 127.0.0.1:5070:5070 \
  ppi-explorer

echo "PPI Explorer deployed on http://127.0.0.1:5070 with root-path /ppi"
