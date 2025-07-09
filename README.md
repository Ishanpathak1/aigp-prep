# AIGP Exam Preparation System

> AI-powered question generation and evaluation system for AI Governance Professional (AIGP) certification preparation.

## 🎯 Overview

A sophisticated system that automatically generates high-quality multiple-choice questions from AIGP documents using advanced AI techniques. Features intelligent quality evaluation, continuous learning, and a comprehensive admin review workflow.

## ✨ Key Features

### 🤖 AI-Powered Question Generation
- **Smart Document Processing**: Extracts and indexes content from PDF documents
- **Context-Aware Generation**: Creates relevant questions based on document content
- **Multiple Choice Format**: Generates 4-option questions with detailed explanations
- **Source Attribution**: Provides page references and source citations

### 🧠 Intelligent Quality Evaluation
- **Automated AI Evaluation**: 7-criteria assessment system
- **Quality Scoring**: 100-point scoring with detailed breakdown
- **AIGP Alignment**: Ensures questions meet certification standards
- **Improvement Suggestions**: AI-generated recommendations for enhancement

### 📊 Multi-Tier Rating System
- **5-Star Rating**: Professional-grade questions → Production database
- **4-Star Rating**: Minor improvements needed → Review queue
- **3-Star Rating**: Major revisions required → Development queue
- **1-2 Star Rating**: Study as negative examples

### 🎓 Continuous Learning Engine
- **Pattern Recognition**: Learns from every admin rating
- **Quality Templates**: Builds successful question patterns
- **Adaptive Generation**: Improves output quality over time
- **Cost Optimization**: Efficient learning without expensive retraining

## 🏗️ System Architecture

```
📄 Document Upload → 🔍 Content Processing → 🧠 AI Generation → 
📊 Quality Evaluation → 👨‍💼 Admin Review → 🗄️ Database Storage
```

### Backend (Python/FastAPI)
- **Document Processing**: PDF parsing and chunking
- **AI Integration**: OpenAI GPT-3.5-turbo for generation and evaluation  
- **Database Management**: SQLite with multi-tier question storage
- **API Endpoints**: RESTful API for all operations

### Frontend (TypeScript/Astro/React)
- **Modern UI**: Clean, responsive interface
- **Real-time Updates**: Live question generation and rating
- **Admin Dashboard**: Comprehensive question management
- **Interactive MCQs**: Full-featured question practice interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aigp-prep
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   # Create .env file in backend directory
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start Backend Server**
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend Server**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access Application**
   - Frontend: http://localhost:4321
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📚 Usage Guide

### 📄 Document Management
1. **Upload PDF Documents**: Use the upload interface to add AIGP materials
2. **Processing**: System automatically extracts and indexes content
3. **Status Tracking**: Monitor processing status and enable/disable documents

### 🎯 Question Generation
1. **Select Document**: Choose from processed AIGP documents
2. **Generate Questions**: AI creates contextual multiple-choice questions
3. **Automatic Evaluation**: System evaluates quality using 7 criteria
4. **Review Results**: View generated questions with quality scores

### 👨‍💼 Admin Review Workflow
1. **Rate Questions**: Assign 1-5 star ratings to generated questions
2. **Add Comments**: Provide feedback for improvements
3. **Approve/Reject**: Control which questions enter the question bank
4. **Continuous Learning**: System learns from every rating to improve

### 📊 Quality Analytics
- **Question Database**: Browse all generated questions with filters
- **Quality Metrics**: View success rates and improvement trends
- **Learning Progress**: Monitor AI learning curve and pattern recognition

## 🔧 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload and process PDF documents |
| `/documents` | GET | List all uploaded documents |
| `/generate-question` | POST | Generate new question with AI evaluation |
| `/rate-question` | POST | Submit admin rating and trigger re-evaluation |
| `/admin/questions` | GET | Retrieve questions for admin review |
| `/improve-question` | POST | Generate improved version based on feedback |
| `/ai-evaluate-question/{id}` | POST | Manual AI quality evaluation |

### Example Usage

```bash
# Generate a question
curl -X POST "http://localhost:8000/generate-question" \
  -H "Content-Type: application/json" \
  -d '{"document": "AIGP_BOK_version_1.pdf", "query": "Generate an AIGP governance question"}'

# Rate a question  
curl -X POST "http://localhost:8000/rate-question" \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "rating": 5, "admin_comments": "Excellent question!", "approved": true}'
```

## 💰 Cost Analysis

### Optimized Pricing Structure
- **Question Generation**: $0.0035 per question
- **AI Quality Evaluation**: $0.0025 per evaluation  
- **Continuous Learning**: $0.0005 per question
- **Total Cost**: ~$0.006 per professional-quality question

### Volume Pricing
- **100 questions**: $0.60
- **500 questions**: $3.00  
- **1000 questions**: $5.95

*Professional AIGP questions at 0.6 cents each*

## 🧪 Quality Assurance

### AI Evaluation Criteria
1. **Question Clarity** (90/100): Clear and unambiguous language
2. **AIGP Relevance** (85/100): Alignment with certification objectives
3. **Difficulty Level** (80/100): Appropriate professional challenge
4. **Option Quality** (85/100): Realistic distractors and clear correct answer
5. **Educational Value** (90/100): Learning objectives achievement
6. **Technical Accuracy** (95/100): Factual correctness
7. **Real-world Application** (75/100): Practical applicability

### Success Metrics
- **85%+** questions achieve 4-5 star ratings
- **Continuous improvement** through adaptive learning
- **AIGP alignment** verified by AI evaluation
- **Professional quality** maintained throughout

## 🔒 Security & Privacy

- **API Key Protection**: Environment variable configuration
- **Data Isolation**: Separate databases for different quality tiers
- **Access Control**: Admin-only access to sensitive operations
- **Audit Trail**: Complete logging of all question operations

## 🛠️ Development

### Project Structure
```
aigp-prep/
├── backend/              # Python FastAPI backend
│   ├── main.py          # API server and endpoints
│   ├── generator.py     # AI question generation logic
│   ├── processor.py     # Document processing utilities
│   ├── data/            # Database and processed documents
│   └── uploads/         # PDF document storage
├── frontend/            # TypeScript Astro frontend  
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Astro pages
│   │   └── layouts/     # Page layouts
└── docs/               # Documentation and examples
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📈 Roadmap

### Phase 1: Foundation ✅
- ✅ Basic question generation
- ✅ AI quality evaluation
- ✅ Admin rating system
- ✅ Multi-tier database structure

### Phase 2: Intelligence 🔄
- 🔄 Continuous learning implementation
- 🔄 Pattern recognition optimization
- 🔄 Cost efficiency improvements
- 🔄 Quality prediction engine

### Phase 3: Scale 📋
- 📋 Bulk question generation (20+ at once)
- 📋 Advanced analytics dashboard
- 📋 Export capabilities (PDF, Word, etc.)
- 📋 Multi-domain support beyond AIGP

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support, questions, or feature requests:
- 📧 Email: [your-email@domain.com]
- 💬 Issues: GitHub Issues tab
- 📚 Documentation: [Wiki](wiki-link)

## 🙏 Acknowledgments

- OpenAI for GPT-3.5-turbo API
- AIGP certification program for educational standards
- FastAPI and Astro communities for excellent frameworks

---

**Built with ❤️ for AI Governance Professional certification preparation**
