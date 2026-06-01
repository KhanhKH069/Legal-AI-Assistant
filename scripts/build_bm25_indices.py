#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.hybrid_retriever import get_hybrid_retriever
import os

os.environ["OFFLINE_MODE"] = "true"

def main():
    print("=" * 60)
    print("  Building BM25 Indices for Hybrid Retrieval")
    print("=" * 60)

    print("\n[1/2] legal_statutory...")
    ret_stat = get_hybrid_retriever("legal_statutory")
    ret_stat.build_bm25()
    
    print("\n[2/2] legal_caselaw...")
    ret_case = get_hybrid_retriever("legal_caselaw")
    ret_case.build_bm25()

    print("\nDONE!")

if __name__ == "__main__":
    main()
