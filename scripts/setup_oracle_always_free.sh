#!/usr/bin/env bash
# Oracle Ampere A1 runs Ubuntu ARM64. The application and all configured
# language runner images are multi-architecture, so the shared Ubuntu setup
# script can deploy the same Compose stack without architecture overrides.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec "$SCRIPT_DIR/setup_aws_free_tier.sh"
