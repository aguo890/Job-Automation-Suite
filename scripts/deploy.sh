#!/bin/bash
# [AI AGENT CONTEXT]: This is the primary CD script. 
# It relies on Docker Compose's native `start-first` configuration and `--wait`.
# If the new container fails its healthcheck, `--wait` will fail, the old container 
# remains active, and the pipeline correctly aborts.

set -e # Exit on any error

echo "🚀 Pulling latest changes..."
git pull origin main
git submodule update --init --recursive

echo "📦 Building and deploying with zero-downtime rolling updates..."
# The --wait flag blocks the script until the new containers report as 'healthy'
# Because we configured 'order: start-first', the old container stays up 
# until the new one is verified.
docker compose up -d --build --wait

echo "✅ Deployment successful and healthy!"
