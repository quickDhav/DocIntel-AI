# DocIntel AI — Document Intelligence + Agentic RAG

A full-stack web application that ingests messy, real-world documents (scanned PDFs, handwritten pages, image-heavy reports, tables, plain text), extracts content accurately, classifies each document using an LLM, and powers a chatbot that answers questions with grounded citations showing the exact source page.

![DocIntel AI](https://img.shields.io/badge/DocIntel-AI-06b6d4?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square) ![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square) ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Chat Page    │  │ Upload Page  │  │ Voice Input      │  │
│  │  • Messages   │  │ • Drag&Drop  │  │ • Web Speech API │  │
│  │  • Citations  │  │ • Progress   │  │ • Live Transcript│  │
│  │  • Thumbnails │  │ • Status     │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Document    │  │  Document    │  │  Agentic RAG      │  │
│  │  Parser      │  │  Classifier  │  │  Engine           │  │
│  │  • pdfplumber│  │  • Gemini    │  │  • ChromaDB       │  │
│  │  • tesseract │  │  • JSON out  │  │  • sentence-trans │  │
│  │  • pdf2image │  │              │  │  • Gemini LLM     │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Security Layer: Encryption, Validation, CORS, Headers ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Storage: SQLite (metadata) │ ChromaDB (vectors) │ Files   │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

### 1. Document Parser
- Handles: scanned PDFs, handwritten pages, PDFs with tables, image-heavy reports, plain text
- **pdfplumber** for digital PDF text + table extraction (tables as structured Markdown)
- **pytesseract** OCR fallback for scanned/image-heavy pages
- **pdf2image** renders every page as a PNG thumbnail
- Per-page output: extracted text, tables, page image, OCR confidence

### 2. Document Classifier
- LLM-powered classification via **Google Gemini 2.0 Flash**
- Multi-dimensional structured JSON output:
  - Document type (invoice, report, form, academic paper, etc.)
  - Topic (finance, healthcare, technology, legal, etc.)
  - Sensitivity level (public, internal, confidential, restricted)
  - Content characteristics (has tables, images, handwriting, etc.)
  - Key entities, date references, summary

### 3. Agentic RAG
- Custom retrieval-augmented generation pipeline
- **ChromaDB** vector store with **sentence-transformers** embeddings (all-MiniLM-L6-v2)
- Top-8 chunk retrieval with document grouping
- **Gemini LLM** synthesis with citation-enforcing system prompt
- Every answer includes inline citations: `[DocName, Page X]`
- Refuses to hallucinate — says "I don't have information" when context is insufficient
- Multi-turn conversation support (last 10 messages)

### 4. Chatbot Page
- Premium dark glassmorphism UI
- Multi-turn conversation with message history
- Each answer displays citation cards with page thumbnails
- Click any thumbnail to view the full page image in a modal
- Smooth animations and micro-interactions

### 5. Bulk Upload Page
- Drag-and-drop multi-file upload zone
- Real-time per-file processing pipeline: `Parsing → Classifying → Indexed`
- Visual status indicators (spinner, checkmark, error)
- Classification results displayed on completion
- Document management (view all, delete)

### 6. Voice Input (Bonus)
- Browser-native **Web Speech API** integration
- Real-time live transcript as user speaks
- Auto-populates chat input on completion
- Visual recording indicator (pulsing microphone)
- Graceful fallback for unsupported browsers

---

## 🛡️ Security Decisions

### Implemented

| Layer | Implementation | Details |
|-------|---------------|---------|
| **Upload** | MIME type validation | Uses `python-magic` for content-based type detection, not just file extensions |
| **Upload** | File size limits | Configurable max (default 50MB), enforced server-side |
| **Upload** | Filename sanitization | Strips path traversal characters, generates UUID-based internal names |
| **Upload** | Allowed type whitelist | Only PDF, PNG, JPG, JPEG, TIFF, TXT accepted |
| **Storage** | Encryption at rest | Fernet (AES-128-CBC) encryption for all uploaded files |
| **Storage** | Memory-only decryption | Files decrypted to memory during processing, never written to disk unencrypted |
| **Storage** | UUID-based file naming | No original filenames on disk, prevents information leakage |
| **Storage** | Non-web-accessible storage | Files stored outside web root, served only through authenticated API |
| **Processing** | Input sanitization | Extracted text sanitized before LLM prompts to prevent prompt injection |
| **Processing** | No code execution | PDF JavaScript disabled, no macro execution during parsing |
| **API** | CORS restrictions | Configurable allowed origins (default: localhost:3000 only) |
| **API** | Security headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Content-Security-Policy |
| **API** | Rate limiting | IP-based rate limiting (120 requests/60 seconds) |
| **API** | No direct file paths | API responses contain only document IDs and page numbers, never file system paths |
| **Code** | No hardcoded secrets | All secrets via `.env` file, `.env.example` provided without real values |

### Considered but Skipped (Time Constraints)

| Security Measure | Reason Skipped |
|-----------------|----------------|
| JWT Authentication | Would add user management complexity; current design uses session-based access suitable for single-user demo |
| Antivirus scanning | Requires ClamAV or similar; file type validation provides baseline protection |
| Database encryption | SQLite stores metadata only (no raw document content); lower risk |
| Request signing | Overkill for demo; would be needed for production multi-tenant deployment |
| Audit logging | Would implement comprehensive audit trail in production |

### Would Add Given More Time

- **JWT + OAuth2 authentication** with role-based access control
- **ClamAV integration** for malware scanning on upload
- **Database encryption** using SQLCipher for SQLite
- **Comprehensive audit logging** (who accessed what, when)
- **Document-level access control** (per-user document permissions)
- **TLS/HTTPS enforcement** at the application level
- **Input/output guardrails** on LLM responses (toxicity filters)
- **Secrets rotation** mechanism for encryption keys
- **Penetration testing** and OWASP Top 10 validation

---

## 🚀 Quick Start

### Prerequisites

```bash
# macOS
brew install poppler tesseract
# Or on Ubuntu/Debian
# sudo apt-get install poppler-utils tesseract-ocr

# Node.js 18+ required
node --version  # Should be >= 18

# Python 3.9+ required
python3 --version  # Should be >= 3.9
```

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/docintel-ai.git
cd docintel-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY from https://aistudio.google.com/apikey

# Start the backend
uvicorn app.main:app --reload --port 8000
```

The backend will:
- Create storage directories automatically
- Initialize the SQLite database
- Generate an encryption key (saved to `.env`)
- Auto-index the 7 sample documents on first run

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local

# Start the frontend
npm run dev
```

### 4. Open the App

Navigate to [http://localhost:3000](http://localhost:3000) — the chatbot is ready with 7 pre-indexed sample documents!

---

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, startup
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy + SQLite
│   │   ├── models.py            # ORM models
│   │   ├── routers/             # API endpoints
│   │   │   ├── upload.py        # File upload + processing
│   │   │   ├── chat.py          # Chat + RAG
│   │   │   ├── documents.py     # Document management
│   │   │   └── pages.py         # Page image serving
│   │   ├── services/            # Business logic
│   │   │   ├── parser.py        # Document parsing engine
│   │   │   ├── classifier.py    # LLM classification
│   │   │   ├── embeddings.py    # Sentence-transformers
│   │   │   ├── vector_store.py  # ChromaDB wrapper
│   │   │   └── rag.py           # RAG engine
│   │   └── utils/               # Security utilities
│   │       ├── encryption.py    # Fernet encryption
│   │       └── file_validation.py # File validation
│   ├── sample_docs/             # 7 pre-included sample documents
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   │   ├── chat/page.tsx    # Chatbot page
│   │   │   ├── upload/page.tsx  # Bulk upload page
│   │   │   └── globals.css      # Design system
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   └── lib/                 # API client + types
│   ├── package.json
│   └── .env.local.example
├── README.md
└── .gitignore
```

## 📦 Sample Documents Included

| # | Document | Type | Tests |
|---|----------|------|-------|
| 1 | Q4 2024 Financial Report | PDF with tables | Table extraction, structured data |
| 2 | AI Safety Research Paper | Multi-page PDF | Long document chunking, citations |
| 3 | Patient Intake Form | PDF form | Form field extraction, sensitive data |
| 4 | Handwritten Meeting Notes | PNG image | OCR, handwriting recognition |
| 5 | Climate Research Notes | Plain text | Text file ingestion |
| 6 | Invoice 2024-0847 | PDF with tables | Invoice parsing, financial data |
| 7 | Smart City Proposal | Multi-page PDF | Mixed content, budget tables |

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload multiple documents |
| `GET` | `/api/upload/status/{job_id}` | Check processing status |
| `POST` | `/api/chat` | Send message, get RAG response |
| `GET` | `/api/chat/history?session_id=` | Get conversation history |
| `POST` | `/api/chat/clear` | Clear conversation history |
| `GET` | `/api/documents` | List all indexed documents |
| `DELETE` | `/api/documents/{doc_id}` | Delete a document |
| `GET` | `/api/pages/{doc_id}/{page_num}` | Get page image |
| `GET` | `/api/pages/{doc_id}/{page_num}/text` | Get page text |
| `GET` | `/api/health` | Health check |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.9+, FastAPI |
| Frontend | Next.js 14, TypeScript |
| PDF Parsing | pdfplumber, pdf2image, pytesseract |
| OCR | Tesseract (via pytesseract) |
| Vector DB | ChromaDB (persistent, local) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Google Gemini 2.0 Flash (free tier) |
| Database | SQLite (via SQLAlchemy) |
| Encryption | cryptography (Fernet/AES) |
| Voice Input | Web Speech API (browser-native) |

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
