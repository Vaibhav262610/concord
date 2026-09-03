# CONCORD Setup Guide

## Quick Start with Docker (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Access services
# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## Local Development Setup

### Prerequisites

- **Python 3.11+** (you have 3.13.3 ✓)
- **Node.js 18+**
- **PostgreSQL 15+**
- **Redis 7+**

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# Install dependencies (this may take 5-10 minutes)
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:** http://localhost:8000  
**API Documentation:** http://localhost:8000/docs

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
copy .env.local.example .env.local

# Start development server
npm run dev
```

**Frontend will be available at:** http://localhost:3000

---

## Docker Compose Setup (Detailed)

### Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# Start specific service
docker-compose up -d postgres
docker-compose up -d redis
docker-compose up -d backend
docker-compose up -d frontend
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Run Migrations in Docker

```bash
# Execute migration in backend container
docker-compose exec backend alembic upgrade head

# Check current migration version
docker-compose exec backend alembic current
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U concord -d concord

# View tables
\dt

# Exit
\q
```

### Redis Access

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Test
PING
# Should return: PONG

# Exit
exit
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (careful: deletes data)
docker-compose down -v
```

---

## Troubleshooting

### Issue: Python dependencies taking too long to install

**Solution:** Some packages need to be compiled. This is normal and may take 10-15 minutes on first install.

If it fails, try installing build tools:

**Windows:**
- Install Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
- Or use pre-built wheels: `pip install --only-binary :all: -r requirements.txt`

**Better solution:** Use Docker (recommended) to avoid compilation issues.

### Issue: Cannot connect to database

**Check PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Restart PostgreSQL:**
```bash
docker-compose restart postgres
```

**Check logs:**
```bash
docker-compose logs postgres
```

### Issue: Port already in use

**Backend (8000):**
```bash
# Windows - find and kill process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

**Frontend (3000):**
```bash
netstat -ano | findstr :3000
taskkill /PID <process_id> /F
```

**Or change ports in docker-compose.yml**

### Issue: Module not found errors

**Solution:** Make sure virtual environment is activated:
```bash
# You should see (venv) in your prompt
.\venv\Scripts\Activate.ps1
```

**Reinstall dependencies:**
```bash
pip install -r requirements.txt
```

---

## Verify Installation

### Option 1: Using Docker

```bash
# Start services
docker-compose up -d

# Check backend health
curl http://localhost:8000/health
# Should return: {"status":"healthy","environment":"development"}

# Check API docs
# Open browser: http://localhost:8000/docs

# Check frontend
# Open browser: http://localhost:3000
```

### Option 2: Using Python Script (After installing dependencies)

```bash
cd backend
python verify_setup.py
```

Expected output:
```
============================================================
CONCORD Phase 1 Verification
============================================================
✓ Checking configuration...
  ✓ Configuration loaded successfully
  ✓ Environment: development
  ✓ Priority weight: 0.6
  ✓ Value weight: 0.4

✓ Checking models...
  ✓ Merchant imported successfully
  ✓ Agent imported successfully
  ✓ Customer imported successfully
  ✓ Policy imported successfully
  ✓ AgentRequest imported successfully
  ✓ Decision imported successfully
  ✓ CustomerContact imported successfully
  ✓ AuditLog imported successfully
  ✓ DelayedAction imported successfully
  ✓ AgentRequest has business value fields (estimated_value, urgency)

✓ Checking database connection...
  ✓ Database connection successful

============================================================
✓ ALL CHECKS PASSED
============================================================
```

---

## Development Workflow

### 1. Start Infrastructure

```bash
# Start PostgreSQL and Redis only
docker-compose up -d postgres redis
```

### 2. Run Backend Locally

```bash
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### 3. Run Frontend Locally

```bash
cd frontend
npm run dev
```

### 4. Make Changes

- Backend code auto-reloads on save
- Frontend auto-reloads on save
- Database changes require new migration:
  ```bash
  alembic revision --autogenerate -m "description"
  alembic upgrade head
  ```

---

## Running Tests

```bash
cd backend
.\venv\Scripts\Activate.ps1
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

---

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://concord:concord_dev_password@localhost:5432/concord
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
OPENAI_API_KEY=your-openai-key-here  # Optional
LOG_LEVEL=INFO
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Production Deployment

### Backend (Railway/Render/Fly.io)

1. Push code to GitHub
2. Connect repository to deployment platform
3. Set environment variables
4. Deploy

**Environment variables to set:**
- `DATABASE_URL` (provided by platform)
- `REDIS_URL` (provided by platform)
- `SECRET_KEY` (generate secure key)
- `ENVIRONMENT=production`
- `OPENAI_API_KEY` (if using AI features)

### Frontend (Vercel)

1. Push code to GitHub
2. Import repository in Vercel
3. Set root directory to `frontend`
4. Set environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
5. Deploy

---

## Next Steps

Once setup is complete:

1. ✅ Verify all services are running
2. ✅ Check API documentation at /docs
3. ✅ Review architecture documentation in docs/architecture.md
4. 🚀 Start Phase 2: Build Agent Gateway

---

## Recommended: Docker-First Approach

For the hackathon, I **strongly recommend using Docker** for development:

### Why?
- ✅ No dependency compilation issues
- ✅ Consistent environment across team
- ✅ Easier to debug
- ✅ Closer to production setup
- ✅ Faster to get started

### How?

```bash
# One command to start everything
docker-compose up -d

# Make code changes
# Backend auto-reloads via volume mount
# Frontend auto-reloads via volume mount

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Run tests
docker-compose exec backend pytest
```

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f <service>`
2. Restart service: `docker-compose restart <service>`
3. Rebuild: `docker-compose up -d --build <service>`
4. Full reset: `docker-compose down -v && docker-compose up -d`

---

**Ready to build CONCORD! 🚀**
