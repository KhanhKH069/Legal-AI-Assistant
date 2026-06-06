import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('results.json', 'r', encoding='utf-8'))
print(f'Total questions: {len(data)}')

empty_docs = [x for x in data if not x.get('relevant_docs')]
empty_arts = [x for x in data if not x.get('relevant_articles')]
bad_name = [x for x in data if any('hieu luc' in d.lower() or 'hiệu lực' in d for d in x.get('relevant_docs', []))]

print(f'Empty relevant_docs: {len(empty_docs)}')
print(f'Empty relevant_articles: {len(empty_arts)}')
print(f'Docs with bad doc_name (hieu luc noise): {len(bad_name)} ({len(bad_name)/len(data)*100:.1f}%)')

# Count articles per question
art_counts = [len(x.get('relevant_articles', [])) for x in data]
print(f'\nArticles per question: min={min(art_counts)}, max={max(art_counts)}, avg={sum(art_counts)/len(art_counts):.1f}')
print(f'Questions with 0 articles: {art_counts.count(0)}')
print(f'Questions with 1-2 articles: {sum(1 for c in art_counts if 1 <= c <= 2)}')
print(f'Questions with 3-5 articles: {sum(1 for c in art_counts if 3 <= c <= 5)}')

# Check doc_name quality
all_docs = []
for x in data:
    all_docs.extend(x.get('relevant_docs', []))

hieu_luc_count = sum(1 for d in all_docs if 'hieu luc' in d.lower() or 'hiệu lực' in d)
print(f'\nTotal doc citations: {len(all_docs)}')
print(f'Citations with bad name "hieu luc...": {hieu_luc_count} ({hieu_luc_count/len(all_docs)*100:.1f}%)')

# Sample bad doc names
unique_bad = list(set(d for d in all_docs if 'hieu luc' in d.lower() or 'hiệu lực' in d))[:8]
print(f'\nSample bad doc entries:')
for b in unique_bad:
    print(f'  - {b}')
