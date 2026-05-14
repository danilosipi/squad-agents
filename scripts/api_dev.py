#!/usr/bin/env python3
"""Sobe a API local com uvicorn (desenvolvimento)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "apps.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
