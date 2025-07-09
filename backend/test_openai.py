 #!/usr/bin/env python3
"""
Test OpenAI API directly
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No OpenAI API key found")
        return False
    
    print(f"🔑 API Key found: {api_key[:20]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        print("🧪 Testing embeddings API...")
        response = client.embeddings.create(
            input=["This is a test text for embedding"],
            model="text-embedding-3-small"
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Embedding successful! Length: {len(embedding)}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai()