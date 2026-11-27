#!/usr/bin/env bash
# ==============================================================================
# CodeAssessment / CodeVedha - One-Click Presentation & Review Launcher
# Authored by: Kantam Pavan Sai Reddy (DevOps & Infrastructure Lead)
# ==============================================================================

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================================${NC}"
echo -e "${CYAN}     CodeAssessment / CodeVedha - Interactive Demo Environment       ${NC}"
echo -e "${CYAN}     Prepared for Capstone & Research Evaluation Review             ${NC}"
echo -e "${CYAN}====================================================================${NC}"

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}[!] Docker daemon is not running. Please start Docker Desktop first.${NC}"
    exit 1
fi

echo -e "\n${CYAN}[1/4] Booting multi-service containerized architecture...${NC}"
docker compose up -d

echo -e "\n${CYAN}[2/4] Waiting for backend API and execution engine to report healthy...${NC}"
ATTEMPTS=0
MAX_ATTEMPTS=20
HEALTHY=false

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    sleep 2
    ATTEMPTS=$((ATTEMPTS+1))
    echo -n "."
done

if [ "$HEALTHY" = true ]; then
    echo -e "\n${GREEN}[✓] Backend API (:8000) is online!${NC}"
else
    echo -e "\n${YELLOW}[!] Backend is still starting up or taking longer than expected.${NC}"
fi

echo -e "\n${CYAN}[3/4] Verifying isolated language runner images...${NC}"
docker images | grep -E "codeassessment|python|gcc|openjdk" || true

echo -e "\n${CYAN}[4/4] Demo Environment Status:${NC}"
echo -e "--------------------------------------------------------------------"
echo -e "  Frontend UI:           ${GREEN}http://localhost:5173${NC} (or :80 in prod)"
echo -e "  FastAPI Docs:          ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Execution Engine:      ${GREEN}http://localhost:8001/health${NC}"
echo -e "  Database:              ${GREEN}PostgreSQL 16 (Port 5432 / Supabase Mumbai)${NC}"
echo -e "--------------------------------------------------------------------"
echo -e "  Demo Student:          username: ${CYAN}student1${NC}   | password: ${CYAN}password${NC}"
echo -e "  Demo Instructor:       username: ${CYAN}instructor1${NC}| password: ${CYAN}password${NC}"
echo -e "--------------------------------------------------------------------"
echo -e "${GREEN}System is ready for tomorrow's review presentation!${NC}\n"
