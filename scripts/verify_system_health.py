#!/usr/bin/env python3
"""System Health & Pre-flight Verification Utility for CodeAssessment.

Authored by: Kantam Pavan Sai Reddy (DevOps & Infrastructure Lead)
Purpose: Automates end-to-end sanity checks across Docker containers,
FastAPI backend (:8000), Execution Engine (:8001), and PostgreSQL database.
"""

import sys
import os
import time
import socket
import urllib.request
import urllib.error
import json

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_status(component: str, ok: bool, details: str = ""):
    symbol = f"{GREEN}[PASS]{RESET}" if ok else f"{RED}[FAIL]{RESET}"
    print(f" {symbol} {component:<32} {details}")


def check_tcp_port(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_http_endpoint(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HealthChecker/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return (resp.status == 200, f"HTTP {resp.status} - {data[:40]}")
    except urllib.error.HTTPError as e:
        return (False, f"HTTP Error {e.code}")
    except urllib.error.URLError as e:
        return (False, f"Connection Failed: {e.reason}")
    except Exception as e:
        return (False, str(e))


def main():
    print(f"\n{BLUE}=================================================================={RESET}")
    print(f"{BLUE}   CodeAssessment / CodeVedha - Pre-flight Health & Sanity Check   {RESET}")
    print(f"{BLUE}   Lead: K. Pavan Sai Reddy | Environment: Local & Cloud Stack    {RESET}")
    print(f"{BLUE}=================================================================={RESET}\n")

    all_passed = True

    # 1. Python Environment Check
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 10)
    print_status("Python Runtime", py_ok, f"v{py_ver} (Target: >= 3.10)")
    if not py_ok:
        all_passed = False

    # 2. Check Backend API (:8000)
    be_port_ok = check_tcp_port("127.0.0.1", 8000)
    if be_port_ok:
        be_http_ok, be_msg = check_http_endpoint("http://127.0.0.1:8000/health")
        print_status("Backend API (:8000)", be_http_ok, be_msg)
        if not be_http_ok:
            all_passed = False
    else:
        print_status("Backend API (:8000)", False, "Port 8000 not listening")
        all_passed = False

    # 3. Check Execution Engine (:8001)
    ee_port_ok = check_tcp_port("127.0.0.1", 8001)
    if ee_port_ok:
        ee_http_ok, ee_msg = check_http_endpoint("http://127.0.0.1:8001/health")
        print_status("Execution Engine (:8001)", ee_http_ok, ee_msg)
        if not ee_http_ok:
            all_passed = False
    else:
        print_status("Execution Engine (:8001)", False, "Port 8001 not listening (Docker engine)")
        all_passed = False

    # 4. Check Frontend Web App (:5173 or :80)
    fe_port_5173 = check_tcp_port("127.0.0.1", 5173)
    fe_port_80 = check_tcp_port("127.0.0.1", 80)
    if fe_port_5173:
        print_status("Frontend UI (:5173)", True, "Vite Dev Server active")
    elif fe_port_80:
        print_status("Frontend UI (:80)", True, "Production Nginx active")
    else:
        print_status("Frontend UI", False, "Neither :5173 nor :80 active")

    # 5. Check Database Connectivity
    db_port_5432 = check_tcp_port("127.0.0.1", 5432)
    db_port_6543 = check_tcp_port("127.0.0.1", 6543)
    if db_port_5432:
        print_status("PostgreSQL (:5432)", True, "Local containerized DB reachable")
    elif db_port_6543:
        print_status("Supabase Pooler (:6543)", True, "Remote transaction pooler reachable")
    else:
        sqlite_file = os.path.exists("backend/codeassessment_v2.db") or os.path.exists("codeassessment_v2.db")
        if sqlite_file:
            print_status("Database (SQLite Fallback)", True, "codeassessment_v2.db file exists")
        else:
            print_status("Database Connection", False, "No active DB port or local sqlite file")

    print(f"\n{BLUE}------------------------------------------------------------------{RESET}")
    if all_passed:
        print(f"{GREEN}✓ All critical pre-flight services are online and ready for demo!{RESET}\n")
        return 0
    else:
        print(f"{YELLOW}⚠ Some services are offline. Run: docker compose up -d to launch stack.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
