import React, { useEffect, useState } from "react";

interface DocumentMeta {
  filename: string;
  processed: boolean;
  enabled: boolean;
}

interface QuestionResponse {
  question: string;
  options?: string[];
  correct_answer?: string;
  explanation?: string;
  detailed_explanations?: { [key: string]: string };
  sources: { source: string; page: number | string }[];
  document_used?: string;
  question_id?: number;
}

const API_BASE = "http://localhost:8000";

const Dashboard: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>("");
  const [question, setQuestion] = useState<QuestionResponse | null>(null);
  const [showSource, setShowSource] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  
  // MCQ state
  const [selectedAnswer, setSelectedAnswer] = useState<string>("");
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  
  // Admin features state
  const [showDetailedExplanations, setShowDetailedExplanations] = useState(false);
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [questionRating, setQuestionRating] = useState<number>(0);
  const [adminComments, setAdminComments] = useState<string>("");

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    setBackendStatus("checking");
    setError("");
    
    try {
      const response = await fetch(`${API_BASE}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors'
      });
      
      if (response.ok) {
        setBackendStatus("online");
        fetchDocuments();
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err: any) {
      setBackendStatus("offline");
      setError(`Backend connection failed: ${err.message}`);
    }
  };

  const fetchDocuments = async () => {
    setLoading(true);
    setError("");
    
    try {
      const response = await fetch(`${API_BASE}/documents`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors'
      });
      
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
        
        if (data.length === 0) {
          setError("No documents uploaded yet. Please upload a PDF file.");
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err: any) {
      setError(`Failed to fetch documents: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      setError("Please select a PDF file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
        mode: 'cors'
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Upload successful! ${data.message}`);
      fetchDocuments();
      } else {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
    } catch (err: any) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const generateQuestion = async () => {
    if (!selectedDoc) {
      setError("Please select a document first");
      return;
    }

    setLoading(true);
    setError("");
    setQuestion(null);
    setSelectedAnswer("");
    setShowResult(false);
    setIsCorrect(null);

    try {
      const response = await fetch(`${API_BASE}/generate-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document: selectedDoc,
          query: "Generate a multiple choice AIGP exam question with 4 options"
        }),
        mode: 'cors'
      });
      
      if (response.ok) {
        const data = await response.json();
        setQuestion(data);
      } else {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
    } catch (err: any) {
      setError(`Failed to generate question: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = () => {
    if (!selectedAnswer || !question) return;
    
    setShowResult(true);
    setIsCorrect(selectedAnswer === question.correct_answer);
  };

  const resetQuestion = () => {
    setSelectedAnswer("");
    setShowResult(false);
    setIsCorrect(null);
    setQuestionRating(0);
    setAdminComments("");
  };

  const rateQuestion = async (rating: number) => {
    if (!question?.question_id) return;
    
    try {
      const response = await fetch(`${API_BASE}/rate-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: question.question_id,
          rating: rating,
          admin_comments: adminComments,
          approved: rating >= 4
        }),
        mode: 'cors'
      });
      
      if (response.ok) {
        setQuestionRating(rating);
        alert(`Question rated ${rating}/5 stars!`);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err: any) {
      setError(`Failed to rate question: ${err.message}`);
    }
  };

  const improveQuestion = async () => {
    if (!question?.question_id || !adminComments) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/improve-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: question.question_id,
          feedback: adminComments
        }),
        mode: 'cors'
      });
      
      if (response.ok) {
        const improvedQuestion = await response.json();
        setQuestion(improvedQuestion);
        setSelectedAnswer("");
        setShowResult(false);
        setIsCorrect(null);
        alert('Question improved successfully!');
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err: any) {
      setError(`Failed to improve question: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const enabledDocs = documents.filter(doc => doc.processed && doc.enabled);

  return (
    <div style={{ 
      minHeight: "100vh", 
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      padding: "2rem"
    }}>
      <div style={{ 
        maxWidth: "1200px", 
        margin: "0 auto",
        background: "white",
        borderRadius: "12px",
        boxShadow: "0 10px 30px rgba(0,0,0,0.1)",
        overflow: "hidden"
      }}>
        
        {/* Header */}
        <div style={{
          background: "linear-gradient(135deg, #2c3e50 0%, #3498db 100%)",
          color: "white",
          padding: "2rem",
          textAlign: "center"
        }}>
          <h1 style={{ margin: 0, fontSize: "2.5rem", fontWeight: "300" }}>
            AIGP Exam Preparation
          </h1>
          <p style={{ margin: "0.5rem 0 0", opacity: 0.9 }}>
            Generate and practice AI governance questions
          </p>
        </div>

        <div style={{ padding: "2rem" }}>
          
          {/* Status Bar */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "1rem",
            background: backendStatus === "online" ? "#d4edda" : "#f8d7da",
            borderRadius: "8px",
            marginBottom: "2rem",
            border: `1px solid ${backendStatus === "online" ? "#c3e6cb" : "#f5c6cb"}`
          }}>
            <div>
              <strong>Status: </strong>
              {backendStatus === "checking" ? "🔄 Checking..." : 
               backendStatus === "online" ? "🟢 Online" : "🔴 Offline"}
            </div>
            {backendStatus !== "online" && (
              <button 
                onClick={checkBackendHealth}
                style={{
                  background: "#007bff",
                  color: "white",
                  border: "none",
                  padding: "0.5rem 1rem",
                  borderRadius: "4px",
                  cursor: "pointer"
                }}
              >
                Retry Connection
              </button>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div style={{
              padding: "1rem",
              marginBottom: "2rem",
              background: "#f8d7da",
              border: "1px solid #f5c6cb",
              borderRadius: "8px",
              color: "#721c24"
            }}>
              ❌ {error}
            </div>
          )}

          {/* Main Content Grid */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 2fr",
            gap: "2rem",
            marginBottom: "2rem"
          }}>
            
            {/* Left Panel - Controls */}
            <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
              
              {/* Upload Section */}
              <div style={{
                padding: "1.5rem",
                border: "2px dashed #ddd",
                borderRadius: "8px",
                textAlign: "center",
                background: "#f8f9fa"
              }}>
                <h3 style={{ marginTop: 0, color: "#495057" }}>📄 Upload Document</h3>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  disabled={uploading || backendStatus !== "online"}
                  style={{
                    margin: "1rem 0",
                    padding: "0.5rem",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    width: "100%"
                  }}
                />
                {uploading && (
                  <div style={{ color: "#007bff", marginTop: "0.5rem" }}>
                    📤 Uploading and processing...
                  </div>
                )}
              </div>

              {/* Question Generation */}
              <div style={{
                padding: "1.5rem",
                border: "1px solid #ddd",
                borderRadius: "8px",
                background: "#ffffff"
              }}>
                <h3 style={{ marginTop: 0, color: "#495057" }}>🎯 Generate Question</h3>
                
                <div style={{ marginBottom: "1rem" }}>
                  <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>
                    Select Document:
                  </label>
                  <select
                    value={selectedDoc}
                    onChange={(e) => setSelectedDoc(e.target.value)}
                    disabled={enabledDocs.length === 0 || backendStatus !== "online"}
                    style={{
                      width: "100%",
                      padding: "0.75rem",
                      border: "1px solid #ddd",
                      borderRadius: "4px",
                      fontSize: "1rem"
                    }}
                  >
                    <option value="">-- Select Document --</option>
                    {enabledDocs.map((doc) => (
                      <option key={doc.filename} value={doc.filename}>
                        {doc.filename.replace('.pdf', '')}
                      </option>
                    ))}
                  </select>
      </div>

                <label style={{ display: "flex", alignItems: "center", marginBottom: "1rem" }}>
        <input
          type="checkbox"
          checked={showSource}
          onChange={(e) => setShowSource(e.target.checked)}
                    style={{ marginRight: "0.5rem" }}
        />
                  Show document sources
      </label>

                <button
                  onClick={generateQuestion}
                  disabled={!selectedDoc || loading || backendStatus !== "online"}
                  style={{
                    width: "100%",
                    padding: "0.75rem",
                    background: loading ? "#6c757d" : "#28a745",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    fontSize: "1rem",
                    cursor: loading ? "not-allowed" : "pointer",
                    fontWeight: "bold"
                  }}
                >
                  {loading ? "🔄 Generating..." : "🎯 Generate Question"}
        </button>
      </div>

              {/* Document Management */}
              <div style={{
                padding: "1.5rem",
                border: "1px solid #ddd",
                borderRadius: "8px",
                background: "#ffffff"
              }}>
                <h3 style={{ marginTop: 0, color: "#495057" }}>
                  📚 Documents ({documents.length})
                </h3>
                
                {documents.length === 0 && !loading && (
                  <p style={{ color: "#6c757d", fontStyle: "italic" }}>
                    No documents uploaded yet
                  </p>
                )}
                
          {documents.map((doc) => (
                  <div key={doc.filename} style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.75rem",
                    marginBottom: "0.5rem",
                    background: doc.enabled ? "#d4edda" : "#f8f9fa",
                    borderRadius: "4px",
                    border: `1px solid ${doc.enabled ? "#c3e6cb" : "#dee2e6"}`
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                        {doc.enabled ? "🟢" : doc.processed ? "🔴" : "⏳"} 
                        {doc.filename.length > 30 ? 
                          doc.filename.substring(0, 30) + "..." : 
                          doc.filename
                        }
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "#6c757d" }}>
                        {doc.processed ? "Ready" : "Processing..."}
                      </div>
                    </div>
      </div>
                ))}
              </div>
            </div>

            {/* Right Panel - Question Display */}
            <div>
              {!question ? (
                <div style={{
                  padding: "3rem",
                  textAlign: "center",
                  border: "2px dashed #ddd",
                  borderRadius: "8px",
                  background: "#f8f9fa",
                  color: "#6c757d"
                }}>
                  <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🎯</div>
                  <h3>No Question Generated</h3>
                  <p>Select a document and click "Generate Question" to start practicing!</p>
                </div>
              ) : (
                <div style={{
                  background: "white",
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                  overflow: "hidden"
                }}>
                  {/* Question Header */}
                  <div style={{
                    background: "#f8f9fa",
                    padding: "1.5rem",
                    borderBottom: "1px solid #ddd"
                  }}>
                    <h3 style={{ margin: 0, color: "#495057" }}>📝 AIGP Practice Question</h3>
                  </div>

                  {/* Question Content */}
                  <div style={{ padding: "2rem" }}>
                    <div style={{
                      fontSize: "1.1rem",
                      lineHeight: "1.6",
                      marginBottom: "2rem",
                      color: "#495057",
                      fontWeight: "500"
                    }}>
                      {question.question}
                    </div>

                    {/* Multiple Choice Options */}
                    {question.options && question.options.length > 0 && (
                      <div style={{ marginBottom: "2rem" }}>
                        {question.options.map((option, index) => {
                          const optionLetter = String.fromCharCode(65 + index); // A, B, C, D
                          const isSelected = selectedAnswer === option;
                          const isCorrect = showResult && option === question.correct_answer;
                          const isWrong = showResult && isSelected && option !== question.correct_answer;
                          
                          return (
                            <div
                              key={index}
                              onClick={() => !showResult && setSelectedAnswer(option)}
                              style={{
                                padding: "1rem",
                                margin: "0.5rem 0",
                                border: `2px solid ${
                                  isCorrect ? "#28a745" : 
                                  isWrong ? "#dc3545" : 
                                  isSelected ? "#007bff" : "#dee2e6"
                                }`,
                                borderRadius: "8px",
                                cursor: showResult ? "default" : "pointer",
                                background: 
                                  isCorrect ? "#d4edda" : 
                                  isWrong ? "#f8d7da" : 
                                  isSelected ? "#e3f2fd" : "#ffffff",
                                transition: "all 0.2s ease"
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "flex-start" }}>
                                <span style={{
                                  background: 
                                    isCorrect ? "#28a745" : 
                                    isWrong ? "#dc3545" : 
                                    isSelected ? "#007bff" : "#6c757d",
                                  color: "white",
                                  width: "24px",
                                  height: "24px",
                                  borderRadius: "50%",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: "0.8rem",
                                  fontWeight: "bold",
                                  marginRight: "1rem",
                                  flexShrink: 0
                                }}>
                                  {optionLetter}
                                </span>
                                <span style={{ flex: 1, lineHeight: "1.4" }}>{option}</span>
                                {showResult && isCorrect && (
                                  <span style={{ color: "#28a745", marginLeft: "1rem" }}>✓</span>
                                )}
                                {showResult && isWrong && (
                                  <span style={{ color: "#dc3545", marginLeft: "1rem" }}>✗</span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
                      {!showResult ? (
                        <button
                          onClick={submitAnswer}
                          disabled={!selectedAnswer}
                          style={{
                            padding: "0.75rem 2rem",
                            background: selectedAnswer ? "#007bff" : "#6c757d",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "1rem",
                            cursor: selectedAnswer ? "pointer" : "not-allowed",
                            fontWeight: "bold"
                          }}
                        >
                          Submit Answer
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={generateQuestion}
                            disabled={loading}
                            style={{
                              padding: "0.75rem 2rem",
                              background: "#28a745",
                              color: "white",
                              border: "none",
                              borderRadius: "4px",
                              fontSize: "1rem",
                              cursor: "pointer",
                              fontWeight: "bold"
                            }}
                          >
                            🎯 New Question
                          </button>
                          <button
                            onClick={resetQuestion}
                            style={{
                              padding: "0.75rem 2rem",
                              background: "#6c757d",
                              color: "white",
                              border: "none",
                              borderRadius: "4px",
                              fontSize: "1rem",
                              cursor: "pointer",
                              fontWeight: "bold"
                            }}
                          >
                            🔄 Try Again
                          </button>
                        </>
                      )}
                    </div>

                    {/* Result Display */}
                    {showResult && (
                      <div style={{
                        padding: "1.5rem",
                        background: isCorrect ? "#d4edda" : "#f8d7da",
                        border: `1px solid ${isCorrect ? "#c3e6cb" : "#f5c6cb"}`,
                        borderRadius: "8px",
                        marginBottom: "1rem"
                      }}>
                        <div style={{
                          fontSize: "1.2rem",
                          fontWeight: "bold",
                          color: isCorrect ? "#155724" : "#721c24",
                          marginBottom: "0.5rem"
                        }}>
                          {isCorrect ? "🎉 Correct!" : "❌ Incorrect"}
                        </div>
                        {!isCorrect && question.correct_answer && (
                          <div style={{ color: "#721c24" }}>
                            The correct answer is: <strong>{question.correct_answer}</strong>
                          </div>
                        )}
                        {question.explanation && (
                          <div style={{
                            marginTop: "1rem",
                            padding: "1rem",
                            background: "rgba(255,255,255,0.7)",
                            borderRadius: "4px",
                            color: "#495057"
                          }}>
                            <strong>Explanation:</strong> {question.explanation}
                          </div>
          )}
        </div>
      )}

                    {/* Sources */}
                    {showSource && question.sources && question.sources.length > 0 && (
                      <div style={{
                        padding: "1rem",
                        background: "#f8f9fa",
                        border: "1px solid #dee2e6",
                        borderRadius: "8px"
                      }}>
                        <h4 style={{ margin: "0 0 0.5rem", color: "#495057" }}>📚 Sources:</h4>
                        {question.sources.map((source, index) => (
                          <div key={index} style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                            • <strong>{source.source}</strong> - Page {source.page}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;




