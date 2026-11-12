#!/usr/bin/env bash
# ==============================================================================
# AWS Free Tier (EC2 t2.micro / t3.micro) 1-Click Deployment Script
# ==============================================================================
set -euo pipefail

echo "========================================================="
echo " Starting CodeAssessment AWS Free Tier Setup & Launch"
echo "========================================================="

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

# 3. Check for .env file
if [ ! -f .env ]; then
    echo "==> Creating .env from .env.example..."
    cp .env.example .env
    # Generate random secrets
    RAND_JWT=$(openssl rand -hex 32 2>/dev/null || tr -dc A-Za-z0-9 </dev/urandom | head -c 64)
    RAND_PG=$(openssl rand -hex 16 2>/dev/null || tr -dc A-Za-z0-9 </dev/urandom | head -c 32)
    sed -i "s/replace-with-at-least-32-random-characters/$RAND_JWT/" .env
    sed -i "s/replace-with-random-hex-password/$RAND_PG/" .env
    echo "==> Generated random JWT_SECRET_KEY and POSTGRES_PASSWORD in .env"
fi

# 4. Build sandbox runner images (Python, C, C++, Java)
echo "==> Building sandbox execution runner images (tools profile)..."
docker compose --profile tools build

# 5. Build and launch application containers
echo "==> Starting application stack (frontend, backend, execution-engine, postgres)..."
docker compose up -d --build

# 6. Verify status
echo "==> Waiting 15 seconds for services to initialize..."
sleep 15
docker compose ps

echo "========================================================="
echo " Deployment Complete!"
echo " Access your application at: http://$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo '<YOUR-EC2-PUBLIC-IP>')"
echo "========================================================="
