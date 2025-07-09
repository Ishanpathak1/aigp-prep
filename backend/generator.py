# generator.py
import json
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_chunks(file_path):
    """Load chunks from JSON file with error handling"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Chunks file not found: {file_path}")
    
    with open(file_path, "r") as f:
        chunks = json.load(f)
    
    if not chunks:
        raise ValueError("No chunks found in the file")
    
    return chunks

def build_index(chunks):
    """Build FAISS index from chunk embeddings"""
    embeddings = np.array([chunk["embedding"] for chunk in chunks]).astype("float32")
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

def search_chunks(query, chunks, index, top_k=5):
    """Search for relevant chunks using embeddings"""
    try:
        print(f"🔍 Searching for relevant chunks with query: {query}")
        
        # Retry logic for embeddings API
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                query_embedding = client.embeddings.create(
                    input=[query],
                    model="text-embedding-3-small"
                ).data[0].embedding
                break  # Success, exit retry loop
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    print(f"⏳ Embeddings rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    raise e

        query_np = np.array([query_embedding]).astype("float32")
        distances, indices = index.search(query_np, top_k)
        
        relevant_chunks = [{
            "chunk": chunks[i]["chunk"],
            "source": chunks[i]["source"],
            "page": chunks[i].get("page", "N/A")
        } for i in indices[0]]
        
        print(f"✅ Found {len(relevant_chunks)} relevant chunks")
        return relevant_chunks
        
    except Exception as e:
        raise Exception(f"Failed to search chunks: {str(e)}")

def generate_question_from_document(document_name, query="Generate an AIGP exam question"):
    """Generate question from specific document with MCQ format"""
    chunks = None
    relevant_chunks = []
    
    try:
        print(f"🎯 Generating question from document: {document_name}")
        
        # Load chunks for the specific document
        chunks_file = os.path.join("data", document_name.replace(".pdf", "_chunks.json"))
        print(f"📂 Loading chunks from: {chunks_file}")
        
        chunks = load_chunks(chunks_file)
        print(f"📦 Loaded {len(chunks)} chunks")
        
        # Build search index
        print("🔨 Building search index...")
        index = build_index(chunks)
        
        # Find relevant chunks using semantic search
        print("🔍 Searching for relevant content...")
        relevant_chunks = search_chunks(query, chunks, index, top_k=5)
        
        if not relevant_chunks:
            raise ValueError("No relevant content found for the query")
        
        # Create context from relevant chunks
        context = "\n\n".join([chunk["chunk"] for chunk in relevant_chunks])
        print(f"📝 Created context with {len(context)} characters")
        
        # Generate MCQ question
        print("🤖 Generating question with OpenAI...")
        prompt = f"""Based on the following content from an AI governance document, create a challenging multiple-choice question suitable for the AIGP (AI Governance Professional) certification exam.

Context:
{context[:3000]}

Requirements:
1. Create a question that tests understanding of AI governance concepts
2. Provide exactly 4 answer options (A, B, C, D)
3. Make sure only one answer is clearly correct
4. Include a detailed explanation for EACH option explaining why it is correct or incorrect
5. The question should be at professional certification level

Format your response as JSON with this exact structure:
{{
    "question": "Your question here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation of why the correct answer is right",
    "detailed_explanations": {{
        "Option A": "Detailed explanation of why this option is correct...",
        "Option B": "Detailed explanation of why this option is incorrect...", 
        "Option C": "Detailed explanation of why this option is incorrect...",
        "Option D": "Detailed explanation of why this option is incorrect..."
    }}
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        # Generate using OpenAI with retry logic for rate limits
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use gpt-3.5-turbo for higher rate limits
                    messages=[
                        {"role": "system", "content": "You are an expert in AI governance and professional certification exam creation. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                break  # Success, exit retry loop
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    print(f"⏳ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    raise e
        
        # Parse the response
        content = response.choices[0].message.content.strip()
        print(f"🎭 OpenAI response: {content[:200]}...")
        
        try:
            # Try to parse as JSON directly
            question_data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                print("⚠️ JSON parsing failed, using fallback question")
                question_data = {
                    "question": "Which of the following is a key principle of AI governance according to the document?",
                    "options": [
                        "Transparency and accountability",
                        "Speed of deployment",
                        "Cost reduction",
                        "Technical complexity"
                    ],
                    "correct_answer": "Transparency and accountability",
                    "explanation": "AI governance emphasizes transparency and accountability as fundamental principles."
                }
        
        # Ensure correct_answer is one of the options
        if question_data.get("correct_answer") not in question_data.get("options", []):
            if question_data.get("options"):
                question_data["correct_answer"] = question_data["options"][0]
        
        # Add sources information
        sources = []
        for chunk in relevant_chunks:
            sources.append({
                "source": chunk["source"],
                "page": chunk["page"]
            })
        
        result = {
            "question": question_data.get("question", ""),
            "options": question_data.get("options", []),
            "correct_answer": question_data.get("correct_answer", ""),
            "explanation": question_data.get("explanation", ""),
            "detailed_explanations": question_data.get("detailed_explanations", {}),
            "sources": sources,
            "document_used": document_name
        }
        
        print("✅ Question generated successfully!")
        return result
        
    except Exception as e:
        print(f"❌ Question generation failed: {str(e)}")
        raise Exception(f"Failed to generate question: {str(e)}")

def evaluate_question_quality(question_data, admin_rating=None, admin_comments=None):
    """AI evaluation of question quality and AIGP alignment"""
    try:
        print(f"🤖 Starting AI evaluation of question...")
        
        # Prepare evaluation prompt
        evaluation_prompt = f"""As an AI Governance Professional (AIGP) certification expert, evaluate the following multiple-choice question for quality, accuracy, and alignment with AIGP standards.

QUESTION TO EVALUATE:
Question: {question_data['question']}

Options:
A) {question_data['options'][0]}
B) {question_data['options'][1]}
C) {question_data['options'][2]}
D) {question_data['options'][3]}

Correct Answer: {question_data['correct_answer']}
Explanation: {question_data['explanation']}

{f'Detailed Explanations: {json.dumps(question_data.get("detailed_explanations", {}), indent=2)}' if question_data.get("detailed_explanations") else ''}

{f'Admin Rating: {admin_rating}/5 stars' if admin_rating else ''}
{f'Admin Comments: {admin_comments}' if admin_comments else ''}

EVALUATION CRITERIA:
1. **Question Clarity**: Is the question clear and unambiguous?
2. **AIGP Relevance**: Does it test relevant AI governance concepts?
3. **Difficulty Level**: Appropriate for professional certification?
4. **Option Quality**: Are distractors realistic and the correct answer clearly best?
5. **Educational Value**: Does it help learners understand key concepts?
6. **Technical Accuracy**: Are all statements technically correct?
7. **Real-world Application**: Can knowledge be applied in practice?

Provide your evaluation in the following JSON format:
{{
    "overall_score": 85,
    "criteria_scores": {{
        "clarity": 90,
        "aigp_relevance": 85,
        "difficulty_level": 80,
        "option_quality": 85,
        "educational_value": 90,
        "technical_accuracy": 95,
        "real_world_application": 75
    }},
    "strengths": [
        "Clear question structure",
        "Relevant to AI governance",
        "Good educational value"
    ],
    "weaknesses": [
        "Could be more challenging",
        "One distractor is too obvious"
    ],
    "improvement_suggestions": [
        "Make option B more plausible by relating it to a common misconception",
        "Add more specific context about regulatory frameworks"
    ],
    "aigp_alignment": "High - directly tests Domain 2 knowledge on AI risk management",
    "recommended_action": "Approve with minor revisions",
    "confidence_level": 92
}}

Return ONLY the JSON object, no other text."""

        # Generate AI evaluation
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert AIGP certification evaluator. Provide detailed, objective analysis of exam questions. Always respond with valid JSON only."},
                        {"role": "user", "content": evaluation_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more consistent evaluation
                    max_tokens=1000
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    print(f"⏳ Rate limit in evaluation, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e

        # Parse AI evaluation response
        content = response.choices[0].message.content.strip()
        print(f"🎭 AI Evaluation response: {content[:200]}...")
        
        try:
            evaluation_result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                evaluation_result = json.loads(json_match.group())
            else:
                # Fallback evaluation
                evaluation_result = {
                    "overall_score": 75,
                    "criteria_scores": {
                        "clarity": 75, "aigp_relevance": 75, "difficulty_level": 75,
                        "option_quality": 75, "educational_value": 75, 
                        "technical_accuracy": 75, "real_world_application": 75
                    },
                    "strengths": ["Question generated successfully"],
                    "weaknesses": ["AI evaluation parsing failed"],
                    "improvement_suggestions": ["Manual review recommended"],
                    "aigp_alignment": "Requires manual verification",
                    "recommended_action": "Manual review needed",
                    "confidence_level": 50
                }

        print(f"✅ AI evaluation completed! Overall Score: {evaluation_result.get('overall_score', 'N/A')}/100")
        
        return evaluation_result
        
    except Exception as e:
        print(f"❌ AI evaluation failed: {str(e)}")
        raise Exception(f"Failed to evaluate question: {str(e)}")

# Keep the old function for backward compatibility
def generate_question_from_query(query, chunks_file="data/all_chunks_combined.json"):
    """Legacy function - use generate_question_from_document instead"""
    try:
        chunks = load_chunks(chunks_file)
        index = build_index(chunks)
        relevant_chunks = search_chunks(query, chunks, index)
        context = "\n\n".join([c["chunk"] for c in relevant_chunks])

        system_prompt = (
            "You're an expert AIGP exam question generator. "
            "Using ONLY the provided context, generate one multiple-choice question with 4 options (A-D) and indicate the correct answer. "
            "Explain the answer briefly after the question. Do not include anything beyond the context."
        )

        user_prompt = f"Context:\n{context}\n\nGenerate the question now."

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        return {
            "question": response.choices[0].message.content.strip(),
            "sources": [{"source": c["source"], "page": c["page"]} for c in relevant_chunks]
        }
    except Exception as e:
        raise Exception(f"Failed to generate question: {str(e)}")


