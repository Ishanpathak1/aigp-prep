from fastapi import FastAPI, UploadFile, File, Query, Body, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

from processor import process_pdf_to_chunks
from generator import generate_question_from_document, evaluate_question_quality

app = FastAPI()

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",  # Astro dev server
        "http://127.0.0.1:4321",  # Alternative localhost
        "http://localhost:3000",  # Alternative port
        "http://localhost:8080",  # Alternative port
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "document_state.json")
DATABASE_FILE = os.path.join(DATA_DIR, "questions.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Database initialization
def init_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Questions table for rating system
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,  -- JSON string
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            detailed_explanations TEXT,  -- JSON string
            sources TEXT,  -- JSON string
            document_used TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            admin_comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved BOOLEAN DEFAULT FALSE,
            version INTEGER DEFAULT 1,
            ai_evaluation TEXT,  -- JSON string with AI evaluation results
            ai_overall_score INTEGER,  -- Quick access to AI score
            ai_evaluated_at TIMESTAMP
        )
    ''')
    
    # Add columns to existing table if they don't exist
    try:
        cursor.execute('ALTER TABLE question_ratings ADD COLUMN ai_evaluation TEXT')
        cursor.execute('ALTER TABLE question_ratings ADD COLUMN ai_overall_score INTEGER') 
        cursor.execute('ALTER TABLE question_ratings ADD COLUMN ai_evaluated_at TIMESTAMP')
    except sqlite3.OperationalError:
        pass  # Columns already exist
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Utility to load/save document state
def load_document_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_document_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ✅ Upload and process PDF
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save file first
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        print(f"📁 Saving file: {file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✅ File saved: {file_path}")
        
        # Update state to show upload but not processed yet
        state = load_document_state()
        state[file.filename] = {
            "processed": False,
            "enabled": False
        }
        save_document_state(state)
        
        # Start processing in background (simplified for now)
        output_path = os.path.join(DATA_DIR, file.filename.replace(".pdf", "_chunks.json"))
        
        try:
            print(f"🔄 Starting processing of {file.filename}")
            process_pdf_to_chunks(file_path, output_path)
            
            # Update state after successful processing
            state[file.filename] = {
                "processed": True,
                "enabled": True
            }
            save_document_state(state)
            print(f"✅ Processing completed: {file.filename}")
            
        except Exception as processing_error:
            print(f"❌ Processing failed: {str(processing_error)}")
            # Keep the file uploaded but mark as failed
            state[file.filename] = {
                "processed": False,
                "enabled": False,
                "error": str(processing_error)
            }
            save_document_state(state)
            
            # Return error but don't fail the upload
            return JSONResponse(
                status_code=200,  # Changed from 500 to 200
                content={
                    "message": "File uploaded but processing failed",
                    "filename": file.filename,
                    "error": str(processing_error),
                    "status": "upload_success_processing_failed"
                }
            )

        return {
            "message": "Uploaded and processed successfully",
            "filename": file.filename,
            "status": "success"
        }
        
    except Exception as upload_error:
        print(f"❌ Upload failed: {str(upload_error)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(upload_error)}")


# ✅ List uploaded documents
@app.get("/documents")
async def list_documents():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".pdf")]
    state = load_document_state()

    documents = []
    for f in files:
        meta = state.get(f, {})
        # Check if chunks file actually exists
        chunks_file = os.path.join(DATA_DIR, f.replace(".pdf", "_chunks.json"))
        actually_processed = os.path.exists(chunks_file)
        
        documents.append({
            "filename": f,
            "processed": actually_processed,
            "enabled": meta.get("enabled", False) and actually_processed
        })

    return documents


# ✅ Toggle document enable/disable
@app.post("/toggle-enable")
async def toggle_document_enable(data: dict = Body(...)):
    filename = data.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    state = load_document_state()
    
    # Check if document exists and is processed
    chunks_file = os.path.join(DATA_DIR, filename.replace(".pdf", "_chunks.json"))
    if not os.path.exists(chunks_file):
        raise HTTPException(status_code=404, detail="Document not found or not processed")

    if filename not in state:
        state[filename] = {"processed": True}
    
    state[filename]["enabled"] = not state[filename].get("enabled", False)
    save_document_state(state)
    return {"message": f"Toggled {filename} to {state[filename]['enabled']}"}


# ✅ Manual re-process (if needed)
@app.post("/ingest")
async def ingest_pdf(filename: str = Query(...)):
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="File not found")

    output_path = os.path.join(DATA_DIR, filename.replace(".pdf", "_chunks.json"))
    
    try:
        process_pdf_to_chunks(pdf_path, output_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Processing failed: {str(e)}"})

    state = load_document_state()
    if filename not in state:
        state[filename] = {}
    state[filename]["processed"] = True
    save_document_state(state)

    return {"message": "Processed", "chunks_file": output_path}


# ✅ Generate Question from selected document
class QuestionRequest(BaseModel):
    document: str
    query: str = "Generate an AIGP exam question"

# Rating system models
class QuestionRating(BaseModel):
    question_id: int
    rating: int  # 1-5
    admin_comments: Optional[str] = None
    approved: Optional[bool] = None

class QuestionImprovement(BaseModel):
    question_id: int
    feedback: str

@app.post("/generate-question")
async def generate_question(req: QuestionRequest):
    try:
        # Verify document is enabled
        state = load_document_state()
        doc_state = state.get(req.document, {})
        
        if not doc_state.get("enabled", False):
            raise HTTPException(status_code=400, detail="Document is not enabled for question generation")
        
        # Check if chunks file exists
        chunks_file = os.path.join(DATA_DIR, req.document.replace(".pdf", "_chunks.json"))
        if not os.path.exists(chunks_file):
            raise HTTPException(status_code=404, detail="Document not processed yet")
        
        result = generate_question_from_document(req.document, req.query)
        
        # Save question to database for rating
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO question_ratings 
            (question_text, options, correct_answer, explanation, detailed_explanations, sources, document_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            result["question"],
            json.dumps(result["options"]),
            result["correct_answer"],
            result["explanation"],
            json.dumps(result.get("detailed_explanations", {})),
            json.dumps(result["sources"]),
            result["document_used"]
        ))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add question_id to response
        result["question_id"] = question_id
        
        # Automatically trigger AI evaluation
        try:
            print("🤖 Triggering automatic AI evaluation...")
            ai_evaluation = evaluate_question_quality(result)
            
            # Save AI evaluation to database
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE question_ratings 
                SET ai_evaluation = ?, ai_overall_score = ?, ai_evaluated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                json.dumps(ai_evaluation),
                ai_evaluation.get('overall_score'),
                question_id
            ))
            conn.commit()
            conn.close()
            
            # Add AI evaluation to response
            result["ai_evaluation"] = ai_evaluation
            print(f"✅ AI evaluation completed with score: {ai_evaluation.get('overall_score', 'N/A')}/100")
            
        except Exception as eval_error:
            print(f"⚠️ AI evaluation failed: {str(eval_error)}")
            # Don't fail the whole request if evaluation fails
            result["ai_evaluation"] = {"error": "AI evaluation failed", "overall_score": None}
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Rate a question
@app.post("/rate-question")
async def rate_question(rating: QuestionRating):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE question_ratings 
            SET rating = ?, admin_comments = ?, approved = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (rating.rating, rating.admin_comments, rating.approved, rating.question_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Trigger AI evaluation after admin rating
        try:
            # Get question data for evaluation
            cursor.execute('''
                SELECT question_text, options, correct_answer, explanation, detailed_explanations
                FROM question_ratings WHERE id = ?
            ''', (rating.question_id,))
            
            question_row = cursor.fetchone()
            if question_row:
                question_data = {
                    "question": question_row[0],
                    "options": json.loads(question_row[1]),
                    "correct_answer": question_row[2],
                    "explanation": question_row[3],
                    "detailed_explanations": json.loads(question_row[4]) if question_row[4] else {}
                }
                
                print("🤖 Triggering AI evaluation after admin rating...")
                ai_evaluation = evaluate_question_quality(
                    question_data, 
                    admin_rating=rating.rating,
                    admin_comments=rating.admin_comments
                )
                
                # Update with AI evaluation
                cursor.execute('''
                    UPDATE question_ratings 
                    SET ai_evaluation = ?, ai_overall_score = ?, ai_evaluated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    json.dumps(ai_evaluation),
                    ai_evaluation.get('overall_score'),
                    rating.question_id
                ))
                
                print(f"✅ AI evaluation completed with score: {ai_evaluation.get('overall_score', 'N/A')}/100")
                
        except Exception as eval_error:
            print(f"⚠️ AI evaluation after rating failed: {str(eval_error)}")
        
        conn.commit()
        conn.close()
        
        return {"message": "Question rated successfully", "question_id": rating.question_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Get all questions for admin review
@app.get("/admin/questions")
async def get_questions_for_review(skip: int = 0, limit: int = 50):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question_text, options, correct_answer, explanation, 
                   detailed_explanations, sources, document_used, rating, 
                   admin_comments, approved, created_at, version,
                   ai_evaluation, ai_overall_score, ai_evaluated_at
            FROM question_ratings 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, skip))
        
        questions = []
        for row in cursor.fetchall():
            questions.append({
                "question_id": row[0],
                "question": row[1],
                "options": json.loads(row[2]),
                "correct_answer": row[3],
                "explanation": row[4],
                "detailed_explanations": json.loads(row[5]) if row[5] else {},
                "sources": json.loads(row[6]),
                "document_used": row[7],
                "rating": row[8],
                "admin_comments": row[9],
                "approved": bool(row[10]) if row[10] is not None else None,
                "created_at": row[11],
                "version": row[12],
                "ai_evaluation": json.loads(row[13]) if row[13] else None,
                "ai_overall_score": row[14],
                "ai_evaluated_at": row[15]
            })
        
        conn.close()
        return {"questions": questions, "total": len(questions)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Improve/regenerate a question
@app.post("/improve-question")
async def improve_question(improvement: QuestionImprovement):
    try:
        # Get original question details
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT document_used FROM question_ratings WHERE id = ?', (improvement.question_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Question not found")
        
        document_used = result[0]
        
        # Generate improved question with feedback incorporated
        improved_query = f"Generate an improved AIGP exam question. Previous feedback: {improvement.feedback}"
        new_result = generate_question_from_document(document_used, improved_query)
        
        # Save as new version
        cursor.execute('''
            SELECT MAX(version) FROM question_ratings WHERE id = ?
        ''', (improvement.question_id,))
        
        current_version = cursor.fetchone()[0] or 1
        new_version = current_version + 1
        
        cursor.execute('''
            INSERT INTO question_ratings 
            (question_text, options, correct_answer, explanation, detailed_explanations, 
             sources, document_used, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_result["question"],
            json.dumps(new_result["options"]),
            new_result["correct_answer"],
            new_result["explanation"],
            json.dumps(new_result.get("detailed_explanations", {})),
            json.dumps(new_result["sources"]),
            new_result["document_used"],
            new_version
        ))
        
        new_question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        new_result["question_id"] = new_question_id
        new_result["version"] = new_version
        new_result["improvement_note"] = f"Improved based on: {improvement.feedback}"
        
        return new_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Manual AI evaluation endpoint
@app.post("/ai-evaluate-question/{question_id}")
async def ai_evaluate_question(question_id: int):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get question data
        cursor.execute('''
            SELECT question_text, options, correct_answer, explanation, 
                   detailed_explanations, rating, admin_comments
            FROM question_ratings WHERE id = ?
        ''', (question_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question_data = {
            "question": result[0],
            "options": json.loads(result[1]),
            "correct_answer": result[2],
            "explanation": result[3],
            "detailed_explanations": json.loads(result[4]) if result[4] else {}
        }
        
        admin_rating = result[5]
        admin_comments = result[6]
        
        # Perform AI evaluation
        ai_evaluation = evaluate_question_quality(
            question_data,
            admin_rating=admin_rating,
            admin_comments=admin_comments
        )
        
        # Save evaluation to database
        cursor.execute('''
            UPDATE question_ratings 
            SET ai_evaluation = ?, ai_overall_score = ?, ai_evaluated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            json.dumps(ai_evaluation),
            ai_evaluation.get('overall_score'),
            question_id
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "AI evaluation completed",
            "question_id": question_id,
            "ai_evaluation": ai_evaluation,
            "overall_score": ai_evaluation.get('overall_score')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




