#!/usr/bin/env python3
"""
Index HR Q&A Documents
"""

import os
import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from services.vector_db import get_vector_db
    print("✅ Import successful!")
except Exception as e:
    print(f"❌ Import error: {e}")
    print("\nTry:")
    print("  pip install chromadb sentence-transformers")
    sys.exit(1)

def parse_qa_markdown(file_path):
    """Parse Q&A from markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    qa_pairs = []
    
    # Split by Q&A blocks (###)
    sections = re.split(r'###\s+Q\d+:', content)
    
    for section in sections[1:]:
        lines = section.strip().split('\n')
        
        qa = {
            'question': '',
            'variations': [],
            'answer': '',
            'file': file_path.name
        }
        
        current_field = None
        answer_lines = []
        
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
                answer_lines.append(line)
        
        qa['answer'] = '\n'.join(answer_lines)
        
        if qa['question']:
            qa_pairs.append(qa)
    
    return qa_pairs

def index_documents():
    """Index all Q&A documents"""
    print("🚀 Indexing HR Q&A to ChromaDB...\n")
    
    # Get vector DB
    vdb = get_vector_db()
    print("✅ Vector DB connected\n")
    
    # Find markdown files
    docs_dir = Path('documents')
    if not docs_dir.exists():
        print("❌ documents/ folder not found!")
        print("Make sure you're running from project root!")
        return
    
    md_files = sorted(docs_dir.glob('*.md'))
    md_files = [f for f in md_files if f.name != 'README.md']
    
    print(f"📁 Found {len(md_files)} document files\n")
    
    total_questions = 0
    total_variations = 0
    
    for md_file in md_files:
        print(f"📄 Processing: {md_file.name}")
        
        # Parse Q&A
        qa_pairs = parse_qa_markdown(md_file)
        
        if not qa_pairs:
            print("  ⚠️  No questions found\n")
            continue
        
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
                'type': 'main'
            }
            metadatas.append(metadata)
            ids.append(f"{md_file.stem}_q{i+1}")
            
            # Variations
            for j, var in enumerate(qa['variations']):
                doc_var = f"Question: {var}\nAnswer: {qa['answer']}"
                documents.append(doc_var)
                
                metadata_var = {
                    'question': var,
                    'answer': qa['answer'],
                    'source_file': qa['file'],
                    'type': 'variation',
                    'original_question': qa['question']
                }
                metadatas.append(metadata_var)
                ids.append(f"{md_file.stem}_q{i+1}_v{j+1}")
            
            total_variations += len(qa['variations'])
        
        # Add to ChromaDB
        try:
            vdb.add(
                collection_name='hr_policies',
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"  ✅ Added {len(qa_pairs)} questions + {sum(len(qa['variations']) for qa in qa_pairs)} variations\n")
            total_questions += len(qa_pairs)
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    print("="*50)
    print("✅ Indexing complete!")
    print(f"📊 Total: {total_questions} questions")
    print(f"📊 Total: {total_variations} variations")
    print("📊 Collection: hr_policies")
    print("="*50)

if __name__ == "__main__":
    index_documents()