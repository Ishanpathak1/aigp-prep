#!/usr/bin/env python3
"""
Debug script to test PDF processing
"""
import fitz  # PyMuPDF
import os

def debug_pdf(pdf_path):
    print(f"🔍 Debugging PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    try:
        # Try to open the PDF
        doc = fitz.open(pdf_path)
        print(f"✅ PDF opened successfully")
        print(f"📄 Number of pages: {len(doc)}")
        print(f"🔒 Is encrypted: {doc.is_encrypted}")
        print(f"📊 Metadata: {doc.metadata}")
        
        # Check first few pages
        for i in range(min(3, len(doc))):
            page = doc[i]
            text = page.get_text()
            print(f"\n--- Page {i+1} ---")
            print(f"Text length: {len(text)}")
            print(f"First 200 chars: {repr(text[:200])}")
            
            if not text.strip():
                print("⚠️ This page appears to be empty or image-only")
                # Try alternative text extraction
                text_dict = page.get_text("dict")
                print(f"Dict extraction blocks: {len(text_dict.get('blocks', []))}")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error opening PDF: {str(e)}")

if __name__ == "__main__":
    pdf_path = "uploads/Mapping emerging critical risks (working paper) 12162024.pdf"
    debug_pdf(pdf_path) 