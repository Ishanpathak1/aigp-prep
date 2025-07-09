import os
import json
from ingest_pdf import process_pdf

DOCS_FOLDER = "docs"
DATA_FOLDER = "data"
COMBINED_FILE = os.path.join(DATA_FOLDER, "all_chunks_combined.json")

def run_batch_ingestion():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    pdf_files = [f for f in os.listdir(DOCS_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("📂 No PDF files found in docs/.")
        return

    print(f"🔍 Found {len(pdf_files)} PDF(s) in {DOCS_FOLDER}/")

    for pdf_file in pdf_files:
        base_name = os.path.splitext(pdf_file)[0]
        output_filename = base_name + "_chunks.json"
        output_path = os.path.join(DATA_FOLDER, output_filename)

        if os.path.exists(output_path):
            print(f"⏩ Skipping already processed: {pdf_file}")
            continue

        input_path = os.path.join(DOCS_FOLDER, pdf_file)
        print(f"\n📄 Processing: {pdf_file}")
        process_pdf(input_path, output_path)

def merge_all_chunks():
    all_chunks = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith("_chunks.json"):
            path = os.path.join(DATA_FOLDER, filename)
            with open(path, "r") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
    with open(COMBINED_FILE, "w") as f:
        json.dump(all_chunks, f, indent=2)
    print(f"\n🧩 Merged {len(all_chunks)} total chunks into {COMBINED_FILE}")

if __name__ == "__main__":
    run_batch_ingestion()
    merge_all_chunks()
