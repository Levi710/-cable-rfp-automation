# PROJECT SHARING GUIDE

## How to Share This Project

There are **3 recommended methods** to share this project so it runs identically on any system.

---

## Method 1: Docker Image Export (RECOMMENDED)

Share as a ready-to-run Docker image. No build required.

### Step 1: Save Docker Images

```bash
cd /Users/soumyajitghosh/cable-rfp-automation

# Build the image first (if not already built)
docker compose build app

# Save all images to a tar file
docker save cable-rfp-automation-app:latest \
  postgres:14-alpine \
  redis:7-alpine \
  qdrant/qdrant:latest \
  jaegertracing/all-in-one:1.55 \
  nginx:alpine \
  -o cable-rfp-docker-images.tar

# This creates a single file: cable-rfp-docker-images.tar (~800MB-1GB)
```

### Step 2: Package Configuration Files

```bash
# Create a distribution package
mkdir cable-rfp-distribution
cd cable-rfp-distribution

# Copy essential files
cp ../docker-compose.yml .
cp ../README.md .
cp ../DEPLOY.md .
cp ../PRODUCTION_READY.md .
cp -r ../data .
cp -r ../deployment .

# Create .env.example
cat > .env.example << 'EOF'
# Database
DATABASE_URL=postgresql://rfp_user:rfp_password@postgres:5432/cable_rfp
POSTGRES_DB=cable_rfp
POSTGRES_USER=rfp_user
POSTGRES_PASSWORD=rfp_password

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Vector Database
QDRANT_URL=http://qdrant:6333

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ENABLE_SCHEDULER=true

# Monitoring
JAEGER_AGENT_HOST=jaeger
EOF

# Create startup script
cat > start.sh << 'EOF'
#!/bin/bash
echo "Starting Cable RFP Automation System..."
docker compose up -d
echo "Waiting for services to initialize..."
sleep 30
echo "System ready!"
echo ""
echo "Run pipeline: docker compose exec -T app python run_pipeline_new.py"
echo "Export results: docker compose exec -T app python export_results.py"
EOF

chmod +x start.sh
```

### Step 3: Create Distribution Package

```bash
# Package everything
cd ..
tar -czf cable-rfp-automation-package.tar.gz cable-rfp-distribution/

# Move the Docker images tar
mv cable-rfp-docker-images.tar cable-rfp-distribution/

# Create final distribution
zip -r cable-rfp-automation-complete.zip cable-rfp-distribution/
```

### Step 4: Share

Share these files:
1. **cable-rfp-automation-complete.zip** (~1.2GB) - Complete package
2. **Installation instructions** (see Recipient Instructions below)

---

## Method 2: Docker Registry (BEST for Teams)

Push to Docker Hub or private registry.

### Setup Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag the image
docker tag cable-rfp-automation-app:latest \
  YOUR_DOCKERHUB_USERNAME/cable-rfp-automation:latest

# Push to Docker Hub
docker push YOUR_DOCKERHUB_USERNAME/cable-rfp-automation:latest
```

### Update docker-compose.yml

```yaml
services:
  app:
    image: YOUR_DOCKERHUB_USERNAME/cable-rfp-automation:latest
    # Remove 'build: .' line
```

### Share Instructions

Recipients only need:
1. `docker-compose.yml`
2. `.env.example` → rename to `.env`
3. Run: `docker compose up -d`

---

## Method 3: Git Repository + Docker Build

Share source code, recipients build locally.

### Prepare Repository

```bash
# Ensure .gitignore is correct
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/
.venv/
venv/

# Environment
.env
*.env.local

# Output
output/
*.log
backup*/

# Docker
*.tar
docker-compose.override.yml

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
temp/
EOF

# Initialize git (if not already)
git init
git add .
git commit -m "Production-ready Cable RFP Automation System"

# Push to GitHub/GitLab
# git remote add origin YOUR_REPO_URL
# git push -u origin main
```

### Share Repository URL

Recipients:
```bash
git clone YOUR_REPO_URL
cd cable-rfp-automation
cp .env.example .env
docker compose up -d
```

---

## RECIPIENT INSTRUCTIONS

### Method 1: Using Docker Image Package

**Requirements:**
- Docker Desktop installed
- 8GB RAM
- 20GB disk space

**Installation Steps:**

```bash
# 1. Extract package
unzip cable-rfp-automation-complete.zip
cd cable-rfp-distribution

# 2. Load Docker images
docker load -i cable-rfp-docker-images.tar

# This will output:
# Loaded image: cable-rfp-automation-app:latest
# Loaded image: postgres:14-alpine
# Loaded image: redis:7-alpine
# ... etc

# 3. Create .env file
cp .env.example .env

# 4. Start system
./start.sh

# OR manually:
docker compose up -d
sleep 30

# 5. Verify
docker compose ps

# 6. Run pipeline
docker compose exec -T app python run_pipeline_new.py

# 7. Export results
docker compose exec -T app python export_results.py

# 8. Download results
docker compose cp app:/app/output/pipeline_results.csv ./results.csv
docker compose cp app:/app/output/pipeline_results.txt ./report.txt
```

### Method 2: Using Docker Hub

```bash
# 1. Create project directory
mkdir cable-rfp-automation
cd cable-rfp-automation

# 2. Download docker-compose.yml
# (Share docker-compose.yml and .env.example separately)

# 3. Create .env file
cp .env.example .env

# 4. Pull and start
docker compose pull
docker compose up -d

# 5. Run pipeline
docker compose exec -T app python run_pipeline_new.py
```

### Method 3: Using Git Repository

```bash
# 1. Clone repository
git clone YOUR_REPO_URL
cd cable-rfp-automation

# 2. Setup environment
cp .env.example .env

# 3. Build and start
docker compose up -d

# 4. Run pipeline
docker compose exec -T app python run_pipeline_new.py
```

---

## File Size Comparison

| Method | Size | Pros | Cons |
|--------|------|------|------|
| **Docker Images** | ~1.2GB | Ready to run, no build | Large file |
| **Docker Hub** | ~800MB | Easy updates, no file transfer | Requires internet |
| **Git Repository** | ~30MB | Small, version control | Requires build (5-10 min) |

---

## What Recipients Get

All methods provide:
- Complete working system
- All 23 requirements implemented
- Main Agent orchestration
- Export to CSV/PDF functionality
- Sample data and documentation
- Production-ready configuration

---

## Recommended Method by Use Case

### For Competition/Demo (Method 1 - Docker Images)
```bash
# You send: cable-rfp-automation-complete.zip
# They run: unzip, docker load, docker compose up -d
# Time to run: 5 minutes
```

### For Team/Collaboration (Method 2 - Docker Hub)
```bash
# You push: docker push to Docker Hub
# They run: docker compose pull && docker compose up -d
# Time to run: 10 minutes
# Benefit: Easy updates
```

### For Development/Open Source (Method 3 - Git)
```bash
# You share: Git repository URL
# They run: git clone && docker compose up -d
# Time to run: 15 minutes
# Benefit: Full source code access
```

---

## Step-by-Step: Recommended Method for Competition

### For You (Sender)

```bash
# 1. Navigate to project
cd /Users/soumyajitghosh/cable-rfp-automation

# 2. Build fresh image
docker compose build app

# 3. Save all images
docker save \
  cable-rfp-automation-app:latest \
  postgres:14-alpine \
  redis:7-alpine \
  qdrant/qdrant:latest \
  jaegertracing/all-in-one:1.55 \
  nginx:alpine \
  -o cable-rfp-images.tar

echo "Saved Docker images: $(du -h cable-rfp-images.tar)"

# 4. Create distribution folder
mkdir -p distribution
cp docker-compose.yml distribution/
cp DEPLOY.md distribution/INSTRUCTIONS.md
cp -r data distribution/
cp -r deployment distribution/
mv cable-rfp-images.tar distribution/

# 5. Create .env.example
cat > distribution/.env.example << 'EOF'
DATABASE_URL=postgresql://rfp_user:rfp_password@postgres:5432/cable_rfp
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOF

# 6. Create startup script
cat > distribution/START_HERE.sh << 'EOF'
#!/bin/bash
echo "================================"
echo "Cable RFP Automation System"
echo "================================"
echo ""
echo "Step 1: Loading Docker images..."
docker load -i cable-rfp-images.tar
echo ""
echo "Step 2: Creating environment..."
cp .env.example .env
echo ""
echo "Step 3: Starting services..."
docker compose up -d
echo ""
echo "Step 4: Waiting for initialization..."
sleep 30
echo ""
echo "================================"
echo "System Ready!"
echo "================================"
echo ""
echo "Run these commands:"
echo "  docker compose exec -T app python run_pipeline_new.py"
echo "  docker compose exec -T app python export_results.py"
echo ""
EOF

chmod +x distribution/START_HERE.sh

# 7. Create README for recipients
cat > distribution/README.txt << 'EOF'
CABLE RFP AUTOMATION SYSTEM
============================

QUICK START:
1. Ensure Docker Desktop is installed and running
2. Run: ./START_HERE.sh
3. Wait for "System Ready!" message
4. Run pipeline: docker compose exec -T app python run_pipeline_new.py
5. Export results: docker compose exec -T app python export_results.py

REQUIREMENTS:
- Docker Desktop
- 8GB RAM
- 20GB disk space
- Windows/Mac/Linux

For detailed instructions, see INSTRUCTIONS.md
EOF

# 8. Create final package
cd ..
tar -czf cable-rfp-automation-v2.0.tar.gz distribution/

echo ""
echo "================================"
echo "Distribution package created!"
echo "================================"
echo ""
echo "File: cable-rfp-automation-v2.0.tar.gz"
echo "Size: $(du -h cable-rfp-automation-v2.0.tar.gz)"
echo ""
echo "Share this file with recipients."
```

### For Recipients

```bash
# 1. Extract package
tar -xzf cable-rfp-automation-v2.0.tar.gz
cd distribution

# 2. Read instructions
cat README.txt

# 3. Run startup script
./START_HERE.sh

# 4. Use the system
docker compose exec -T app python run_pipeline_new.py
docker compose exec -T app python export_results.py

# 5. Get results
docker compose cp app:/app/output/pipeline_results.csv ./results.csv
open results.csv
```

---

## Verification

After recipient sets up, they should verify:

```bash
# Check all containers running
docker compose ps

# Expected: 6 containers running
# - app
# - postgres  
# - redis
# - qdrant
# - jaeger
# - nginx

# Run pipeline (should complete in ~1.4 seconds)
docker compose exec -T app python run_pipeline_new.py

# Export results
docker compose exec -T app python export_results.py

# Verify output files exist
docker compose exec -T app ls -lh output/
```

---

## Troubleshooting for Recipients

### Issue: Docker images not loading

```bash
# Check if tar file is complete
ls -lh cable-rfp-images.tar

# Try loading again
docker load -i cable-rfp-images.tar
```

### Issue: Containers not starting

```bash
# Check Docker resources
docker info | grep -E "CPUs|Memory"

# Ensure 8GB RAM allocated
# Docker Desktop > Settings > Resources > Memory
```

### Issue: Pipeline fails

```bash
# Check logs
docker compose logs app

# Restart
docker compose restart app
docker compose exec -T app python run_pipeline_new.py
```

---

## Security Notes

### Before Sharing:

1. **Remove sensitive data**
   ```bash
   # Ensure no .env file in distribution
   rm distribution/.env
   
   # Only include .env.example
   ```

2. **Check for secrets**
   ```bash
   grep -r "password\|secret\|key" distribution/ --exclude="*.md"
   ```

3. **Clean output folder**
   ```bash
   # Remove any previous results
   rm -rf distribution/output/*
   ```

---

## Summary

**Recommended for Competition Submission:**

**Method 1: Docker Image Package**

Advantages:
- Recipients don't need to build anything
- Guaranteed to work identically
- Includes all dependencies
- Single command to run

Steps:
1. You: Create package with `docker save` (10 minutes)
2. You: Share tar.gz file (~1.2GB)
3. Recipient: Extract and run `./START_HERE.sh` (5 minutes)
4. Recipient: System is ready to use

**The system will run identically on any machine with Docker installed.**

---

## Quick Reference

### Create Distribution Package
```bash
docker compose build app
docker save cable-rfp-automation-app:latest postgres:14-alpine redis:7-alpine qdrant/qdrant:latest jaegertracing/all-in-one:1.55 nginx:alpine -o images.tar
# Package with docker-compose.yml and scripts
```

### Recipient Usage
```bash
docker load -i images.tar
docker compose up -d
docker compose exec -T app python run_pipeline_new.py
docker compose exec -T app python export_results.py
```

**That's it! The system is portable and ready to share.**
