import json
import chromadb
from chromadb.utils import embedding_functions

def main():
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    
    print("Loading legal_qa.json...")
    with open("data/raw/legal_qa.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    collection = client.get_or_create_collection(
        name="legal_qa",
        embedding_function=emb_fn
    )
    
    ids = []
    documents = []
    metadatas = []
    
    for item in data:
        ids.append(item["id"])
        # Embed Question + Answer
        documents.append(f"Câu hỏi: {item['question']}\nTrả lời: {item['answer']}")
        metadatas.append({
            "category": item.get("category", ""),
            "source": item.get("source", ""),
            "question": item["question"]
        })
        
    print(f"Upserting {len(ids)} QA pairs into ChromaDB...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print("Done! legal_qa collection is ready.")

if __name__ == "__main__":
    main()
