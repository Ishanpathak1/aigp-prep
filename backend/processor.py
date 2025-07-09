# processor.py
import fitz  # PyMuPDF
import json
import os
from uuid import uuid4
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with enhanced error handling"""
    try:
        doc = fitz.open(pdf_path)
        texts = []
        
        print(f"📖 PDF Info: {len(doc)} pages, encrypted: {doc.is_encrypted}")
        
        if doc.is_encrypted:
            print("🔒 PDF is encrypted, attempting to unlock...")
            if not doc.authenticate(""):  # Try empty password
                raise Exception("PDF is password protected")
        
        for i, page in enumerate(doc):
            print(f"📄 Processing page {i + 1}/{len(doc)}")
            
            # Try multiple text extraction methods
            text = page.get_text()
            
            if not text.strip():
                print(f"⚠️ Page {i + 1} has no text, trying alternative extraction...")
                # Try dictionary method for better text extraction
                text_dict = page.get_text("dict")
                blocks = text_dict.get("blocks", [])
                alt_text = ""
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line.get("spans", []):
                                alt_text += span.get("text", "") + " "
                text = alt_text
            
            if text.strip():
                texts.append({"page": i + 1, "text": text.strip()})
                print(f"✅ Page {i + 1}: {len(text)} characters extracted")
            else:
                print(f"⚠️ Page {i + 1}: No text found (might be image-only)")
        
        doc.close()
        
        if not texts:
            raise Exception("No text content found in any page. This might be a scanned PDF or image-only document.")
        
        print(f"✅ Successfully extracted text from {len(texts)} pages")
        return texts
        
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def chunk_text(text, max_words=300):
    """Split text into chunks with better handling"""
    if not text or not text.strip():
        return []
    
    words = text.split()
    if len(words) == 0:
        return []
    
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk.strip())
    
    return chunks

def embed_chunk(text):
    """Generate embedding for text chunk"""
    try:
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")

def process_pdf_to_chunks(pdf_path, output_path):
    """Process PDF to chunks with embeddings - fixed version"""
    try:
        chunks = []
        print(f"📖 Extracting text from {os.path.basename(pdf_path)}")
        pages = extract_text_from_pdf(pdf_path)
        
        if not pages:
            raise Exception("No text content found in PDF")
        
        print(f"📄 Found {len(pages)} pages")
        
        # Process pages in batches to avoid memory issues
        batch_size = 10  # Process 10 pages at a time
        total_chunks = 0
        
        for i in range(0, len(pages), batch_size):
            batch_pages = pages[i:i + batch_size]
            print(f"🔄 Processing pages {i+1}-{min(i+batch_size, len(pages))} of {len(pages)}")
            
            for page in batch_pages:
                try:
                    print(f"📝 Processing page {page['page']}: {len(page['text'])} characters")
                    text_chunks = chunk_text(page["text"])
                    print(f"📦 Created {len(text_chunks)} chunks for page {page['page']}")
                    
                    for chunk_idx, chunk_content in enumerate(text_chunks):
                        if chunk_content.strip():  # Only process non-empty chunks
                            print(f"🔄 Processing chunk {total_chunks + 1} (page {page['page']}, chunk {chunk_idx + 1})")
                            
                            # Add retry logic for embeddings
                            max_retries = 3
                            for retry in range(max_retries):
                                try:
                                    embedding = embed_chunk(chunk_content)
                                    chunks.append({
                                        "id": str(uuid4()),
                                        "source": os.path.basename(pdf_path),
                                        "page": page["page"],
                                        "chunk": chunk_content,
                                        "embedding": embedding
                                    })
                                    total_chunks += 1
                                    print(f"✅ Chunk {total_chunks} processed successfully")
                                    break
                                except Exception as embed_error:
                                    if retry == max_retries - 1:
                                        print(f"❌ Final embedding failure for chunk: {str(embed_error)}")
                                        raise embed_error
                                    print(f"⚠️ Embedding retry {retry + 1}/{max_retries}: {str(embed_error)}")
                                    time.sleep(1)  # Wait before retry
                        else:
                            print(f"⚠️ Skipping empty chunk {chunk_idx + 1} on page {page['page']}")
                                    
                except Exception as page_error:
                    print(f"⚠️ Skipping page {page['page']} due to error: {str(page_error)}")
                    continue
        
        print(f"📊 Processing Summary: {total_chunks} total chunks created")
        
        if not chunks:
            raise Exception("No valid chunks generated from PDF")
        
        print(f"💾 Saving {len(chunks)} chunks to {output_path}")
        with open(output_path, "w") as f:
            json.dump(chunks, f, indent=2)
        print(f"✅ Saved {len(chunks)} chunks to {output_path}")
        
    except Exception as e:
        print(f"❌ Processing error: {str(e)}")
        raise Exception(f"Failed to process PDF: {str(e)}")
