import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('results.json', 'r', encoding='utf-8'))

# Check the source_note field in ChromaDB to understand what's happening
# Look at sample good vs bad doc entries
print("=== DOC NAME QUALITY ANALYSIS ===")
all_docs = []
for x in data:
    all_docs.extend(x.get('relevant_docs', []))

good = [d for d in all_docs if 'hieu luc' not in d.lower() and 'hiệu lực' not in d]
bad  = [d for d in all_docs if 'hieu luc' in d.lower() or 'hiệu lực' in d]

print(f"Good doc_name: {len(good)} ({len(good)/len(all_docs)*100:.1f}%)")
print(f"Bad doc_name : {len(bad)} ({len(bad)/len(all_docs)*100:.1f}%)")
print("\nSample GOOD entries:")
for d in list(set(good))[:10]:
    print(f"  {d}")

# Check article number quality
all_arts = []
for x in data:
    all_arts.extend(x.get('relevant_articles', []))

print(f"\n=== ARTICLE CITATIONS ===")
print(f"Total: {len(all_arts)}")

# Check article number format
import re
proper_dieu = [a for a in all_arts if re.search(r'Điều \d+', a)]
print(f"Has proper 'Điều XX': {len(proper_dieu)} ({len(proper_dieu)/len(all_arts)*100:.1f}%)")

# Sample articles
print("\nSample articles (first 5):")
for x in data[:2]:
    for a in x.get('relevant_articles', []):
        print(f"  {a}")

# Check source_note_text pattern more carefully - extract what doc_name looks like
print("\n=== SOURCE NOTE PATTERN ===")
# Load parquet to see actual column content
try:
    import pandas as pd
    df = pd.read_parquet('data/raw/phapdien_articles.parquet')
    print("Parquet columns:", list(df.columns))
    print("\nSample source_note_text:")
    for v in df['source_note_text'].dropna().unique()[:5]:
        print(f"  {str(v)[:200]}")
except Exception as e:
    print(f"Cannot read parquet: {e}")
