# KYC Document Validation & Risk Scoring System

A full-stack, AI-powered KYC (Know Your Customer) Document Validation & Risk Scoring system built with Next.js, FastAPI, and open-source AI tools. This system supports document upload, OCR, entity extraction, AI-based validation, explainable risk scoring, and automated decisions.

## Features

- **Document Upload & Management**: Secure document upload with validation and status tracking
- **OCR Processing**: PaddleOCR integration with confidence scoring
- **Entity Extraction**: spaCy-based NER for extracting Name, DOB, Address, and ID Number
- **LLM Validation**: GPT-4o-mini powered cross-document validation and fraud detection
- **Risk Scoring**: Transparent, weighted risk scoring (0-100) with human-readable explanations
- **Workflow Orchestration**: n8n integration for automated processing workflows
- **User & Admin Dashboards**: Professional FinTech-style UI with audit trails
- **Storage Abstraction**: Support for both local filesystem and MinIO (S3-compatible)

## Tech Stack

### Frontend
- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **ShadCN/UI** components

### Backend
- **FastAPI** (Python)
- **PostgreSQL** database
- **SQLAlchemy** ORM
- **Alembic** migrations

### AI/ML
- **PaddleOCR** for text extraction
- **spaCy** for Named Entity Recognition
- **GPT-4o-mini** (OpenAI) for document validation
- **Rule-based** risk scoring engine

### Infrastructure
- **Docker Compose** for containerization
- **n8n** for workflow orchestration
- **MinIO** for S3-compatible object storage

## Project Structure

```
Ai-KYC/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, storage
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic (OCR, NER, LLM, risk scoring)
│   │   └── schemas/        # Pydantic schemas
│   └── requirements.txt
├── frontend/               # Next.js application
│   ├── app/               # App Router pages
│   ├── components/        # React components
│   ├── lib/               # Utilities, API client
│   └── types/             # TypeScript types
├── n8n/                   # n8n workflows
│   └── workflows/         # Exportable workflow JSON
├── data/                  # Synthetic KYC documents
│   └── synthetic/         # Generated test documents
├── scripts/               # Utility scripts
│   └── generate_synthetic_data.py
├── docker-compose.yml     # Container orchestration
└── README.md
```

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm
- **Docker** and Docker Compose
- **PostgreSQL** (or use Docker Compose)
- **OpenAI API Key** (for GPT-4o-mini)

## Setup Instructions

### 1. Clone and Navigate

```bash
cd Ai-KYC
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy English model
python -m spacy download en_core_web_sm

# Copy environment variables
cp .env.example .env

# Edit .env and set your configuration
# - DATABASE_URL
# - SECRET_KEY (generate a secure random string)
# - OPENAI_API_KEY
# - STORAGE_TYPE (local or minio)
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local (optional, defaults to http://localhost:8000)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 4. Start Infrastructure (Docker Compose)

```bash
# From project root
docker-compose up -d

# This starts:
# - MinIO on ports 9000 (API) and 9001 (Console)
# - n8n on port 5678
# 
# Note: PostgreSQL is not included if using Neon cloud database.
# If you need local PostgreSQL, uncomment the postgres service in docker-compose.yml
```

### 5. Initialize Database

```bash
cd backend

# Create database tables
python -c "from app.main import app; from app.core.database import engine; from app.models import base; base.Base.metadata.create_all(bind=engine)"
```

### 6. Start Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start FastAPI server
# Use --host 0.0.0.0 to allow connections from Docker containers
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Generate Synthetic Data

To generate test KYC documents:

```bash
cd scripts
python generate_synthetic_data.py 10  # Generate 10 sets of documents
```

Documents will be created in `data/synthetic/person_1/`, `person_2/`, etc.

## n8n Workflow Setup

1. Access n8n at `http://localhost:5678`
2. Login with credentials: `admin` / `admin`
3. Import the workflow from `n8n/workflows/kyc-workflow.json`
4. Configure the webhook URL to match your backend configuration
5. Activate the workflow

## Usage

### User Flow

1. **Register/Login**: Create an account or sign in
2. **Create Application**: Click "New Application" to start a KYC process
3. **Upload Documents**: Upload ID card, passport, proof of address, etc.
4. **View Status**: Monitor processing status and risk scores
5. **Review Results**: See extracted entities, OCR results, and AI validation

### Admin Flow

1. **Access Admin Dashboard**: Navigate to `/admin` (requires admin role)
2. **View All Applications**: See all KYC applications with filters
3. **Review Applications**: View detailed risk scores and validation results
4. **Manual Override**: Approve or reject applications manually
5. **Audit Trail**: View complete audit logs for compliance

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### KYC
- `POST /api/kyc/applications` - Create new KYC application
- `GET /api/kyc/applications` - List user's applications
- `GET /api/kyc/applications/{id}` - Get application details
- `POST /api/kyc/applications/{id}/documents` - Upload document
- `GET /api/kyc/documents/{id}` - Get document details

### Admin
- `GET /api/admin/applications` - List all applications (admin only)
- `POST /api/admin/applications/{id}/approve` - Manually approve
- `POST /api/admin/applications/{id}/reject` - Manually reject
- `GET /api/admin/applications/{id}/audit` - Get audit logs

## Risk Scoring

The risk scoring engine evaluates applications based on:

- **Name Mismatch** (25% weight): Consistency of names across documents
- **DOB Mismatch** (20% weight): Consistency of dates of birth
- **Address Mismatch** (15% weight): Consistency of addresses
- **Low OCR Confidence** (20% weight): Quality of document OCR
- **Missing Documents** (20% weight): Completeness of required documents
- **Fraud Signals** (30% weight): AI-detected suspicious patterns

**Decision Thresholds:**
- **0-30**: APPROVED (automatically approved)
- **31-60**: REVIEW (requires manual review)
- **61-100**: REJECTED (automatically rejected)

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kyc_db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
STORAGE_TYPE=local  # or "minio"
STORAGE_PATH=./storage

# MinIO (if using)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=kyc-documents
MINIO_SECURE=false

# OpenAI
OPENAI_API_KEY=sk-...

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/kyc-process
N8N_API_KEY=

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Development

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Production Deployment

1. Set secure environment variables
2. Use production database (managed PostgreSQL)
3. Configure proper CORS origins
4. Use MinIO or AWS S3 for document storage
5. Set up SSL/TLS certificates
6. Configure reverse proxy (nginx)
7. Use process manager (PM2, systemd) for backend
8. Build and deploy frontend as static site or use Next.js server

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens for authentication
- File upload validation (type, size)
- SQL injection protection via SQLAlchemy
- CORS configuration
- Input validation with Pydantic

## Compliance & Data

- **Synthetic Data Only**: All test documents are generated synthetically
- **No Real PII**: Never use real personal information
- **Audit Trails**: All actions are logged for compliance
- **Explainable AI**: Risk scores include human-readable reasoning

## Troubleshooting

### Backend Issues

- **Database Connection**: Ensure PostgreSQL is running and DATABASE_URL is correct
- **OCR Errors**: Install PaddleOCR dependencies: `pip install paddlepaddle paddleocr`
- **spaCy Model**: Download with `python -m spacy download en_core_web_sm`
- **OpenAI API**: Verify API key is set and has credits

### Frontend Issues

- **API Connection**: Check NEXT_PUBLIC_API_URL matches backend URL
- **CORS Errors**: Verify CORS_ORIGINS includes frontend URL
- **Build Errors**: Clear `.next` folder and rebuild

### Docker Issues

- **Port Conflicts**: Change ports in docker-compose.yml
- **Volume Permissions**: Ensure Docker has write access to volumes
- **Container Logs**: Use `docker-compose logs` to debug

## License

This project is open-source and available for portfolio, interview, and MVP demonstration purposes.

## Contributing

This is a demonstration project. For production use, consider:
- Adding comprehensive tests
- Implementing rate limiting
- Adding monitoring and logging
- Enhancing error handling
- Adding more document types
- Improving OCR accuracy
- Adding multi-language support

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.

