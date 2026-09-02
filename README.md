# CONCORD

**"Make autonomous agents act as one."**

## Overview

Concord is a customer-level control plane for autonomous AI agent fleets. It coordinates multiple specialized agents (Cart Recovery, Payment Recovery, Subscription, Upsell) to ensure they act cohesively on each customer.

### Core Concept

Individual agents decide **WHAT THEY WANT TO DO**.  
Concord decides **WHETHER, WHEN, AND HOW THEY SHOULD ACT**.

## Key Features

- **Customer-level Consent Management** - Global opt-out enforcement
- **Communication Frequency Control** - Prevent customer fatigue
- **Cross-agent Priority Arbitration** - Smart conflict resolution
- **Offer Validation** - Enforce merchant discount policies
- **Action Merging** - Combine compatible requests
- **Delayed Actions** - Queue requests when limits are reached
- **Agent Permissions** - Fine-grained authorization
- **Audit Trail** - Complete decision history
- **Explainable Decisions** - Every decision has a clear reason
- **Fleet Analytics** - Measure coordination impact

## Architecture

```
AI AGENTS
    ↓
AGENT GATEWAY (Authentication, Validation, Idempotency)
    ↓
ARBITRATION ENGINE
    ├── Consent Manager
    ├── Frequency Manager
    ├── Priority Engine
    ├── Conflict Detector
    ├── Offer Validator
    ├── Merge Engine
    └── Decision Engine
    ↓
DECISION: ALLOW | BLOCK | DELAY | MERGE
```

**Important:** The LLM provides advisory input (semantic conflict detection, message merging). The deterministic policy engine has final authority over all business decisions.

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Alembic (migrations)

### Frontend
- Next.js 14+
- TypeScript
- Tailwind CSS
- shadcn/ui

### Infrastructure
- Docker & Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

## Project Structure

```
concord/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── routes/    # API endpoints
│   │   ├── services/  # Business logic
│   │   ├── ai/        # LLM integration
│   │   └── tests/     # Test suite
│   └── alembic/       # Database migrations
├── frontend/          # Next.js frontend
├── docs/              # Documentation
└── docker-compose.yml
```

## API Endpoints

### Agent Actions
- `POST /api/v1/actions` - Submit agent action request
- `GET /api/v1/actions` - List action requests
- `GET /api/v1/actions/{id}` - Get specific request

### Decisions
- `GET /api/v1/decisions` - List decisions
- `GET /api/v1/decisions/{id}` - Get decision details

### Customers
- `GET /api/v1/customers` - List customers
- `GET /api/v1/customers/{id}` - Get customer state and history

### Agents
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Register new agent

### Policies
- `GET /api/v1/policies` - Get merchant policies
- `PUT /api/v1/policies` - Update merchant policies

### Simulation
- `POST /api/v1/simulation/run` - Run fleet simulation

### Analytics
- `GET /api/v1/analytics/overview` - Dashboard metrics

### Audit
- `GET /api/v1/audit/{customer_id}` - Customer audit timeline

## Running Tests

```bash
cd backend
pytest
```

## Demo Scenarios

The system includes simulated agents for demonstration:

1. **Cart Recovery Agent** - Sends cart abandonment reminders with discounts
2. **Payment Recovery Agent** - Handles failed payment retries
3. **Subscription Recovery Agent** - Manages subscription renewals
4. **Upsell Agent** - Promotes additional products

Run the fleet simulation to see Concord in action:
- Navigate to `/simulation` in the dashboard
- Click "Run Fleet Simulation"
- Watch real-time arbitration across 1000+ requests

## Key Decisions

### ALLOW
Payment recovery request meets all criteria - customer contacted immediately.

### BLOCK
Upsell offer exceeds merchant's maximum discount policy - request rejected.

### DELAY
Customer reached daily contact limit - request queued for tomorrow.

### MERGE
Cart recovery + compatible upsell combined into single message - better customer experience.

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/concord
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key-here  # Optional
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Documentation

- [Architecture](docs/architecture.md) - System design and data flow
- [API Reference](docs/api.md) - Complete API documentation
- [Product Spec](docs/product.md) - Product requirements and use cases

## Development Phases

- [x] Phase 1: Foundation (Models, Migrations, Docker)
- [ ] Phase 2: Agent Gateway (Authentication, Validation)
- [ ] Phase 3: Arbitration Engine (Consent, Frequency, Priority)
- [ ] Phase 4: Conflict Detection & Merging
- [ ] Phase 5: Audit & Analytics
- [ ] Phase 6: Simulation Engine
- [ ] Phase 7: Frontend Dashboard
- [ ] Phase 8: LLM Integration
- [ ] Phase 9: Polish & Documentation

## Contributing

This is a hackathon MVP. Focus areas:
- Arbitration engine correctness
- Test coverage for business logic
- Clear decision explanations
- Real metrics (no fake data)

## License

MIT
