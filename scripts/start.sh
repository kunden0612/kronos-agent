#!/bin/bash

echo "Starting Kronos-Agent services..."
docker compose up -d --build

echo "Waiting for services to start..."
sleep 10

echo "Services started!"
echo ""
echo "Access URLs:"
echo "- Kronos API: http://localhost:8001"
echo "- Kronos API Docs: http://localhost:8001/docs"
echo "- MinIO Console: http://localhost:9001"
echo ""
echo "Default credentials:"
echo "- MinIO: minioadmin / minioadmin"
echo "- PostgreSQL: kronos / kronos"
