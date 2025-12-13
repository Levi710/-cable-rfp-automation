#!/bin/bash

echo "========================================"
echo "Cable RFP Automation System"
echo "========================================"
echo ""
echo "Requirements:"
echo "  - Docker Desktop installed and running"
echo "  - 8GB RAM available"
echo "  - 20GB disk space"
echo ""
read -p "Press Enter to continue..."

echo ""
echo "[1/4] Loading Docker images..."
echo "(This may take 3-5 minutes)"
docker load -i cable-rfp-images.tar

echo ""
echo "[2/4] Creating environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   Created .env file"
else
    echo "   .env file already exists"
fi

echo ""
echo "[3/4] Starting services..."
docker compose up -d

echo ""
echo "[4/4] Waiting for initialization (30 seconds)..."
sleep 30

echo ""
echo "========================================"
echo "System Ready!"
echo "========================================"
echo ""
echo "Run these commands to use the system:"
echo ""
echo "  1. Run pipeline:"
echo "     docker compose exec -T app python run_pipeline_new.py"
echo ""
echo "  2. Export results:"
echo "     docker compose exec -T app python export_results.py"
echo ""
echo "  3. Download results:"
echo "     docker compose cp app:/app/output/pipeline_results.csv ./results.csv"
echo "     docker compose cp app:/app/output/pipeline_results.txt ./report.txt"
echo ""
echo "  4. View results:"
echo "     open results.csv  # macOS"
echo "     start results.csv # Windows"
echo ""
echo "For detailed documentation, see:"
echo "  - INSTRUCTIONS.md"
echo "  - README.md"
echo ""
