import fitz  # PyMuPDF
import json
from uuid import uuid4
from tqdm import tqdm
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            texts.append({"page": i + 1, "text": text})
    return texts

def chunk_text(text, max_words=300):
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def embed_chunk(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def process_pdf(pdf_path, output_path):
    chunks = []
    pages = extract_text_from_pdf(pdf_path)
    for page in tqdm(pages, desc=f"Processing {os.path.basename(pdf_path)}"):
        for chunk in chunk_text(page["text"]):
            embedding = embed_chunk(chunk)
            chunks.append({
                "id": str(uuid4()),
                "source": os.path.basename(pdf_path),
                "page": page["page"],
                "chunk": chunk,
                "embedding": embedding
            })
    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"\n✅ Saved {len(chunks)} chunks to {output_path}")

# === USAGE EXAMPLE ===
# Uncomment this line to process one file:
process_pdf("docs/AIGP_BOK_version_1.pdf", "data/aigp_chunks.json")

