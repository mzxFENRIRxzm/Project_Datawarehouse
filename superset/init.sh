#!/bin/bash
set -euo pipefail
superset db upgrade
/app/.venv/bin/python /app/pythonpath/bootstrap_admin.py
superset init
