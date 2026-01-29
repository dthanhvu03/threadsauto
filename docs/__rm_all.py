#!/usr/bin/env python3
"""Delete all old documentation directories"""
import shutil
from pathlib import Path

docs = Path(__file__).parent
dirs = [
    'archive',
    'architecture',
    'code-reviews',
    'deployment',
    'guides',
    'migration',
    'troubleshooting',
    'future',
    'examples',
    'schemas',
    'templates',
]

deleted = 0
for d in dirs:
    p = docs / d
    if p.exists() and p.is_dir():
        try:
            shutil.rmtree(str(p))
            print(f"✅ Deleted: {d}/")
            deleted += 1
        except Exception as e:
            print(f"❌ Failed to delete {d}/: {e}")

print(f"\n✅ Deleted {deleted} directories")
