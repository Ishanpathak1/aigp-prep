#!/usr/bin/env python3
"""
Dedicated server startup script
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("Create a .env file in the backend directory with:")
        print("OPENAI_API_KEY=your_api_key_here")
        exit(1)
    
    print("🚀 Starting backend server...")
    print(f"🔑 OpenAI API Key: {'✅ Set' if api_key else '❌ Not set'}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 