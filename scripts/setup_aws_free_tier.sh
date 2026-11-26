#!/usr/bin/env bash
# ==============================================================================
# Ubuntu VM demo deployment script (AWS/Oracle/other VPS, Ubuntu 22.04/24.04)
# ==============================================================================
set -euo pipefail

echo "========================================================="
echo " Starting CodeAssessment Ubuntu VM Setup & Launch"
echo "========================================================="

# Health checks and public-IP reporting use curl even when Docker was already
# installed before this script was run.
if ! command -v curl &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y curl
fi

# 1. Setup 4 GB Swap Space (Essential for 1 GB RAM Free Tier instances)
SWAP_TOTAL=$(free -m | awk '/^Swap:/ {print $2}')
if [ "$SWAP_TOTAL" -lt 2000 ]; then
    echo "==> Configuring 4 GB swap space to prevent Out-Of-Memory issues..."
    if [ ! -f /swapfile ]; then
        sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        sudo sysctl vm.swappiness=10
        echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
        echo "==> 4 GB Swap space configured successfully."
    fi
else
    echo "==> Swap space is already configured ($SWAP_TOTAL MB)."
fi

# 2. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "==> Installing Docker and Docker Compose..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release git
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "==> Docker installed successfully."
fi

# A newly-added docker group is not active in the current shell. Use sudo for
# this run when the daemon socket is not yet available to the current user.
if docker info >/dev/null 2>&1; then
    DOCKER=(docker)
else
    DOCKER=(sudo docker)
fi
"${DOCKER[@]}" info >/dev/null

# 3. Check for .env file
if [ ! -f .env ]; then
    echo "==> Creating .env from .env.example..."
    cp .env.example .env
    # Generate random secrets
    RAND_JWT=$(openssl rand -hex 32 2>/dev/null || tr -dc A-Za-z0-9 </dev/urandom | head -c 64)
    RAND_PG=$(openssl rand -hex 16 2>/dev/null || tr -dc A-Za-z0-9 </dev/urandom | head -c 32)
    sed -i "s/replace-with-at-least-32-random-characters/$RAND_JWT/" .env
    sed -i "s/replace-with-random-hex-secret/$RAND_PG/" .env
    echo "==> Generated random JWT_SECRET_KEY and POSTGRES_PASSWORD in .env"
fi

if grep -q 'replace-with-' .env; then
    echo "ERROR: .env still contains placeholder secrets. Replace them before deployment." >&2
    exit 1
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "==> Created backend/.env. Add GROQ_API_KEY there to enable optional AI feedback."
fi

# 4. Pull the runtime images used by the active execution engine
echo "==> Pulling sandbox language runtime images..."
"${DOCKER[@]}" pull python:3.11-slim
"${DOCKER[@]}" pull gcc:13
"${DOCKER[@]}" pull eclipse-temurin:17-jdk
"${DOCKER[@]}" pull node:20-slim

# 5. Build and launch application containers
echo "==> Starting application stack (frontend, backend, execution-engine, postgres)..."
"${DOCKER[@]}" compose up -d --build

# 6. Verify status
echo "==> Waiting for the application health check..."
for attempt in $(seq 1 36); do
    if curl --fail --silent http://127.0.0.1/health >/dev/null; then
        break
    fi
    if [ "$attempt" -eq 36 ]; then
        "${DOCKER[@]}" compose ps
        "${DOCKER[@]}" compose logs --tail=100 backend execution-engine
        echo "ERROR: application did not become healthy within three minutes." >&2
        exit 1
    fi
    sleep 5
done
"${DOCKER[@]}" compose ps

echo "========================================================="
echo " Deployment Complete!"
echo " Access your application at: http://$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo '<YOUR-EC2-PUBLIC-IP>')"
echo " Only ports 22 (your IP), 80, and optionally 443 should be allowed by the EC2 security group."
echo "========================================================="
