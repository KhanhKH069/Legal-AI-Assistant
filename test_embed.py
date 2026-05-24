import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

os.environ["GOOGLE_API_KEY"] = "AIzaSyB_hFc2JgVaIDDQ7B8O6xUxWcELvHXD0rk"
emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
docs = ["hello", "world"]
res = []
for doc in docs:
    res.append(emb.embed_query(doc))
print(f"Docs: {len(docs)}, Embeddings: {len(res)}")
