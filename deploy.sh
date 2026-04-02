#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "==> Stopping existing containers..."
docker-compose down

echo "==> Rebuilding images..."
docker-compose build --no-cache

echo "==> Starting containers..."
docker-compose up -d

echo "==> Done."
docker-compose ps
