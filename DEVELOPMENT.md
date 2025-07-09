# Development Guide

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+ (recommended: 3.11+)
- Node.js 16+ (recommended: 18+)
- OpenAI API key with GPT-3.5-turbo access

### Environment Setup

1. **Clone and Setup Virtual Environment**
   ```bash
   git clone <your-repo-url>
   cd aigp-prep
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate     # Windows
   ```

2. **Install Backend Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Create Environment Configuration**
   ```bash
   # Create .env file in backend directory
   cat > .env << EOF
   OPENAI_API_KEY=your_openai_api_key_here
   DEBUG=True
   LOG_LEVEL=INFO
   EOF
   ```

4. **Install Frontend Dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

## 🚀 Running the Application

### Backend Development Server
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development Server
```bash
cd frontend
npm run dev
```

### Access Points
- **Frontend**: http://localhost:4321
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redoc Documentation**: http://localhost:8000/redoc

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📂 Project Structure

```
aigp-prep/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── generator.py         # Question generation logic
│   ├── processor.py         # Document processing
│   ├── data/               # Database and processed files
│   ├── uploads/            # Uploaded PDF storage
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Astro pages
│   │   └── layouts/        # Page layouts
│   ├── package.json        # Node.js dependencies
│   └── astro.config.mjs    # Astro configuration
├── docs/                   # Documentation files
├── scripts/                # Utility scripts
└── README.md              # Main documentation
```

## 🔧 Development Workflow

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement Changes**
   - Backend changes in `backend/`
   - Frontend changes in `frontend/src/`
   - Update tests as needed

3. **Test Changes**
   ```bash
   # Test backend
   cd backend && python -m pytest
   
   # Test frontend
   cd frontend && npm test
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Open PR against main branch
   - Include detailed description
   - Ensure all tests pass

## 🐛 Debugging

### Backend Debugging
- **Logs**: Check console output for detailed error messages
- **Database**: Use SQLite browser to inspect `backend/data/questions.db`
- **API Testing**: Use FastAPI docs at http://localhost:8000/docs

### Frontend Debugging
- **Browser Console**: Check for JavaScript errors
- **Network Tab**: Monitor API requests
- **React DevTools**: Install browser extension for component debugging

### Common Issues

**OpenAI API Errors:**
```bash
# Check API key is set
echo $OPENAI_API_KEY

# Test API connection
cd backend
python test_openai.py
```

**Port Conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000

# Use different port
uvicorn main:app --port 8001
```

## 📊 Database Schema

### Questions Table
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    options TEXT NOT NULL,        -- JSON array
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    detailed_explanations TEXT,   -- JSON object
    sources TEXT,                 -- JSON array
    document_used TEXT,
    created_at TIMESTAMP,
    rating INTEGER,               -- 1-5 stars
    admin_comments TEXT,
    approved BOOLEAN,
    ai_evaluation TEXT,           -- JSON object
    version INTEGER DEFAULT 1
);
```

## 🔄 API Endpoints

### Core Endpoints
- `POST /upload` - Upload PDF documents
- `GET /documents` - List processed documents
- `POST /generate-question` - Generate new question
- `POST /rate-question` - Submit admin rating
- `GET /admin/questions` - Admin question review
- `POST /improve-question` - Generate improved version
- `POST /ai-evaluate-question/{id}` - AI evaluation

### Development Endpoints
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /redoc` - Alternative API docs

## 🏗️ Architecture Notes

### AI Integration
- **OpenAI GPT-3.5-turbo**: Question generation and evaluation
- **Text Embeddings**: Document similarity search
- **FAISS Vector Store**: Efficient semantic search

### Quality Control
- **7-Criteria Evaluation**: Automated quality assessment
- **Multi-tier Rating**: Questions sorted by quality level
- **Continuous Learning**: Pattern recognition from ratings

### Cost Optimization
- **Efficient Prompting**: Minimal token usage
- **Caching**: Reuse successful patterns
- **Batch Processing**: Group operations where possible

## 📝 Contributing Guidelines

1. **Code Style**
   - Python: Follow PEP 8
   - TypeScript: Use Prettier formatting
   - Comments: Document complex logic

2. **Commit Messages**
   - Use conventional commits format
   - Example: `feat: add bulk question generation`

3. **Testing**
   - Add tests for new features
   - Maintain test coverage above 80%

4. **Documentation**
   - Update README for user-facing changes
   - Update this guide for developer changes
   - Include code comments for complex functions

## 🚨 Security Considerations

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Use `.env` for sensitive configuration
- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Implement to prevent abuse
- **CORS**: Configure properly for production

## 📈 Performance Optimization

### Backend
- **Database Indexing**: Add indexes for frequently queried fields
- **Connection Pooling**: For high-traffic scenarios
- **Caching**: Redis for frequently accessed data
- **Async Operations**: Use FastAPI's async capabilities

### Frontend
- **Code Splitting**: Lazy load components
- **Image Optimization**: Compress and serve appropriate formats
- **Bundle Analysis**: Monitor bundle size
- **CDN**: Use for static assets in production

---

Happy coding! 🚀 