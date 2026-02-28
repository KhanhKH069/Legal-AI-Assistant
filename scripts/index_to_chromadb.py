#!/usr/bin/env python3
"""
Index HR Q&A documents to ChromaDB
"""

import os
import re
import sys
from pathlib import Path

# Add src to path (adjust based on project structure)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hr-ai-agent-pure-vector', 'src'))

try:
    from services.vector_db import get_vector_db
except ImportError:
    print("⚠️  Note: Run from project root or adjust path")
    print("This is a template script - modify paths as needed")
    sys.exit(1)

def parse_qa_markdown(file_path):
    """Parse Q&A from markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    qa_pairs = []
    
    # Split by Q&A blocks (###)
    sections = re.split(r'###\s+Q\d+:', content)
    
    for section in sections[1:]:  # Skip first (header)
        lines = section.strip().split('\n')
        
        qa = {
            'title': '',
            'question': '',
            'variations': [],
            'answer': '',
            'file': file_path.name
        }
        
        # Parse section
        current_field = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('**Câu hỏi:**'):
                current_field = 'question'
                qa['question'] = line.replace('**Câu hỏi:**', '').strip()
            elif line.startswith('**Biến thể:**'):
                current_field = 'variations'
            elif line.startswith('**Trả lời:**'):
                current_field = 'answer'
            elif line.startswith('---'):
                break
            elif line.startswith('- ') and current_field == 'variations':
                qa['variations'].append(line[2:])
            elif current_field == 'answer' and line:
                qa['answer'] += line + '\n'
        
        if qa['question']:
            qa_pairs.append(qa)
    
    return qa_pairs

def index_documents(docs_dir='./'):
    """Index all Q&A documents"""
    print("🚀 Indexing HR Q&A to ChromaDB...")
    
    # Get vector DB
    vdb = get_vector_db()
    
    # Find all markdown files
    md_files = list(Path(docs_dir).glob('*.md'))
    md_files = [f for f in md_files if f.name != 'README.md']
    
    total_questions = 0
    
    for md_file in sorted(md_files):
        print(f"\n📄 Processing: {md_file.name}")
        
        # Parse Q&A
        qa_pairs = parse_qa_markdown(md_file)
        
        # Prepare for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, qa in enumerate(qa_pairs):
            # Main question
            doc = f"Question: {qa['question']}\nAnswer: {qa['answer']}"
            documents.append(doc)
            
            metadata = {
                'question': qa['question'],
                'answer': qa['answer'],
                'source_file': qa['file'],
                'variations': '|'.join(qa['variations'])
            }
            metadatas.append(metadata)
            
            ids.append(f"{md_file.stem}_q{i+1}")
            
            # Add variations as separate docs (point to same answer)
            for var in qa['variations']:
                doc_var = f"Question: {var}\nAnswer: {qa['answer']}"
                documents.append(doc_var)
                
                metadata_var = metadata.copy()
                metadata_var['is_variation'] = True
                metadata_var['original_question'] = qa['question']
                metadatas.append(metadata_var)
                
                ids.append(f"{md_file.stem}_q{i+1}_var{qa['variations'].index(var)}")
        
        # Add to ChromaDB
        vdb.add(
            collection_name='hr_policies',
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"  ✅ Added {len(qa_pairs)} questions + {sum(len(qa['variations']) for qa in qa_pairs)} variations")
        total_questions += len(qa_pairs)
    
    print(f"\n{'='*50}")
    print("✅ Indexing complete!")
    print(f"📊 Total: {total_questions} core questions")
    print("📊 Collection: hr_policies")
    print(f"{'='*50}")

if __name__ == "__main__":
    index_documents()
