#!/usr/bin/env python3
"""
HR AI Agent
"""

import logging
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print(" HR AI AGENT")
print("=" * 80)
print()

try:
    from services.vector_db import get_vector_db

    print(" Testing Vector Database...")
    vdb = get_vector_db()

    print(" Vector DB initialized!")
    print(f" Collections: {len(vdb.collections)}")
    for name, collection in vdb.collections.items():
        count = collection.count()
        print(f"   - {name}: {count} documents")

    print()
    print(" System ready!")
    print()
    print(" Next steps:")
    print("  - Web UI: streamlit run streamlit_app.py")
    print("  - Add documents to: documents/ folder")
    print("  - Index: python scripts/ingest_documents.py")

except ImportError as e:
    print(f" Missing package: {e}")
except Exception as e:  # noqa: BLE001
    print(f"  Note: {e}")
    print()
    print("This is normal for first run.")
    print("Add documents and index them to get started!")

print("=" * 80)