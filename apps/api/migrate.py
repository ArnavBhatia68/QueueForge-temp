#!/usr/bin/env python3
"""
Standalone migration runner for Railway pre-deploy.
Run as: python migrate.py
"""
import os
import sys

# Ensure the app root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command

if __name__ == "__main__":
    alembic_cfg = Config("alembic.ini")
    print("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete.")
