import fitz
from app.services.chunking import chunk_text
from app.services.embeddings import generate_embeddings
import numpy as np

doc = fitz.open(r'C:\Users\Acer\Downloads\PIXELCRAFT_Rubrics Round 2.pdf')
text = doc[0].get_text()
raw_chunks = chunk_text(text, 800, 120)
chunks = [' '.join(c.split()) for c in raw_chunks if ' '.join(c.split())]

print(f"Generated {len(chunks)} chunks for Pixelcraft Rubrics:")
for i, c in enumerate(chunks):
    print(f"-- CHUNK {i} ({len(c)} chars) --")
    print(c[:200] + "...")

chunk_embeddings = generate_embeddings(chunks)

queries = [
    "what are the rubrics of pixel craft",
    "what are the rubrics of pixelcraft",
    "pixelcraft rubrics round 2",
    "criteria for judging pixelcraft"
]

query_embeddings = generate_embeddings(queries)

for q, q_emb in zip(queries, query_embeddings):
    print(f"\nQuery: '{q}'")
    for i, (c, c_emb) in enumerate(zip(chunks, chunk_embeddings)):
        dot = np.dot(q_emb, c_emb)
        norm_q = np.linalg.norm(q_emb)
        norm_c = np.linalg.norm(c_emb)
        cos_sim = dot / (norm_q * norm_c)
        print(f"  Chunk {i}: cosine_similarity = {cos_sim:.4f} (pass >= 0.5? {cos_sim >= 0.5})")
