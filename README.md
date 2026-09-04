# CONCORD - Agent Fleet Control Plane

> **Intelligent Multi-Agent Communication Orchestration System**  
> Built for Razorpay AI Buildathon 2026

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black)](https://nextjs.org/)

---

 ██████╗ ██████╗ ███╗   ██╗ ██████╗ ██████╗ ██████╗ ██████╗ 
██╔════╝██╔═══██╗████╗  ██║██╔════╝██╔═══██╗██╔══██╗██╔══██╗
██║     ██║   ██║██╔██╗ ██║██║     ██║   ██║██████╔╝██║  ██║
██║     ██║   ██║██║╚██╗██║██║     ██║   ██║██╔══██╗██║  ██║
╚██████╗╚██████╔╝██║ ╚████║╚██████╗╚██████╔╝██║  ██║██████╔╝
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ 

##  What is CONCORD?

**CONCORD** solves the chaos of multiple AI agents trying to contact the same customer simultaneously. 

Imagine you have 4 autonomous agents:
- 💰 Payment Recovery Bot (high priority, urgent)
- 📧 Marketing Bot (medium priority, promotional)
- 🎧 Support Bot (high priority, help)
- 📱 Transactional Bot (critical, notifications)

**The Problem**: All 4 try to send messages to the same customer within 2 minutes. The customer gets spammed!

**CONCORD's Solution**: 
1. **Detects conflicts** between agents
2. **Intelligently merges or prioritizes** requests
3. **Ensures optimal customer experience**
4. **Tracks everything** for compliance

---

## 🚀 Key Features

### 1. Intelligent Arbitration Engine
- **13-step decision process** evaluating every request
- Checks consent, frequency limits, priority, business value
- Returns ALLOW, BLOCK, DELAY, or MERGE decisions
- Prevents customer fatigue

### 2. Conflict Detection & Resolution
- **4 Conflict Types**: Simultaneous, Rapid Succession, Channel Overlap, Intent Conflict
- **7 Merge Strategies**: Prioritize highest, combine messages, delay conflicting, etc.
- Automatic conflict resolution with manual override

### 3. Fleet Simulation System
- **4 Agent Types**: Payment Recovery, Marketing, Support, Transactional
- **6 Test Scenarios**: High volume, mixed priority, conflicting agents, etc.
- Run realistic simulations at 0.1x to 100x speed
- Perfect for testing and demos

### 4. Complete Observability
- Customer analytics (30-day activity breakdown)
- Audit trail for compliance (every action logged)
- Real-time metrics dashboard
- Delivery tracking across 4 channels (Email, SMS, WhatsApp, Push)

### 5. Professional Dashboard
- 8-page React dashboard
- Customer management
- Live simulation interface
- Decision monitoring
- Execution tracking

---

## 🏗️ Architecture

```
┌─────────────┐
│   Agents    │  Multiple autonomous bots
└──────┬──────┘
       │ API Requests
       ↓
┌─────────────┐
│   Gateway   │  Auth, validation, idempotency
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Arbitration │  13-step decision engine
│   Engine    │  • Consent check
│             │  • Frequency limits
│             │  • Conflict detection ← NEW!
│             │  • Priority scoring
│             │  • Policy enforcement
└──────┬──────┘
       │ ALLOW/BLOCK/DELAY/MERGE
       ↓
┌─────────────┐
│  Execution  │  Multi-channel delivery
│    Layer    │  Email, SMS, WhatsApp, Push
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Customer   │  End recipient
└─────────────┘
```

---

## 📊 Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 15
- Redis 7
- SQLAlchemy ORM
- Pydantic validation
- Alembic migrations

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide Icons

**Infrastructure:**
- Docker & Docker Compose
- Nginx-ready
- Environment-based config

---

## 🎬 Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd concord

# Start all services
docker-compose up -d

# Wait 30 seconds for services to initialize
# Then access:
```

**🌐 Frontend Dashboard**: http://localhost:3000  
**🔧 Backend API**: http://localhost:8000  
**📚 API Documentation**: http://localhost:8000/docs

That's it! The system is ready to use.

---

## 🎮 How to Test (For Judges)

### Option 1: Run a Simulation (Recommended - 2 minutes)

1. Open http://localhost:3000
2. Click **"Simulation"** in the left sidebar
3. Select **"Conflicting Agents"** scenario
4. Set parameters:
   - Customers: 10
   - Duration: 300 seconds
   - Speed: 10x (completes in 30 seconds)
5. Click **"Run Simulation"**
6. Watch as 40+ requests are processed with conflict detection!

**What you'll see:**
- Total requests processed
- Allow/Block/Delay/Merge breakdown
- Requests by agent type
- Decision distribution
- Sample decisions with scores

### Option 2: Manual API Testing (3 minutes)

1. Open API docs: http://localhost:8000/docs

2. **Create an agent:**
   ```
   POST /api/v1/agents
   {
     "name": "Test Agent",
     "agent_type": "payment_recovery"
   }
   ```
   Copy the `api_key` from response.

3. **Submit action request:**
   ```
   POST /api/v1/actions
   Headers: X-API-Key: <your-api-key>
   {
     "request_id": "test-001",
     "customer_id": "CUST001",
     "action": "SEND_MESSAGE",
     "intent": "PAYMENT_RECOVERY",
     "channel": "EMAIL",
     "priority": 85,
     "message": "Payment reminder"
   }
   ```

4. **Check decision:**
   ```
   GET /api/v1/decisions
   ```

### Option 3: Explore Dashboard (5 minutes)

Navigate through all pages:
- **Overview** - System stats
- **Agents** - Register and manage agents
- **Customers** - Customer analytics
- **Decisions** - See arbitration results
- **Executions** - Track deliveries
- **Metrics** - Delivery success rates
- **Simulation** - Run test scenarios

---

## 📈 What Makes CONCORD Special?

### 1. **Industry-First Conflict Resolution**
No other system detects and resolves multi-agent conflicts in real-time. We built:
- 4 conflict detection algorithms
- 7 intelligent merge strategies
- Automatic + manual resolution

### 2. **Comprehensive Simulation**
Test your agent fleet before going live:
- 4 realistic agent simulators
- 6 pre-built scenarios
- Variable speed (0.1x - 100x)
- Detailed analytics

### 3. **Production-Ready Architecture**
- 50+ REST API endpoints
- 11 database models with relationships
- Complete audit trail
- Scalable design

### 4. **Full Observability**
Every action is:
- Logged in audit trail
- Tracked in customer analytics
- Available via timeline APIs
- Searchable and filterable

---

## 🎯 Use Cases

### E-commerce Platform
**Problem**: Payment recovery bot and marketing bot both target same customer.  
**Solution**: CONCORD prioritizes payment recovery, delays marketing by 24 hours.

### Banking App
**Problem**: 3 agents send notifications within 1 minute (transaction alert, bill reminder, offer).  
**Solution**: CONCORD combines non-urgent messages, sends transaction alert immediately.

### SaaS Platform
**Problem**: Support agent and marketing agent conflict during trial period.  
**Solution**: CONCORD prioritizes support, blocks marketing until issue resolved.

---

## 📊 Key Metrics

- **API Endpoints**: 50+
- **Database Models**: 11
- **Frontend Pages**: 8
- **Test Scenarios**: 6
- **Agent Simulators**: 4
- **Merge Strategies**: 7
- **Conflict Types**: 4
- **Delivery Channels**: 4
- **Lines of Code**: ~15,000+

---

## 🔧 API Endpoints Overview

### Core Operations
- `POST /api/v1/agents` - Register agent
- `POST /api/v1/actions` - Submit request
- `GET /api/v1/decisions` - List decisions
- `GET /api/v1/executions` - Track deliveries

### Conflict Management (NEW)
- `GET /api/v1/conflicts` - List conflicts
- `GET /api/v1/conflicts/{id}/recommendation` - Get merge strategy
- `POST /api/v1/conflicts/{id}/merge` - Execute merge

### Simulation (NEW)
- `GET /api/v1/simulation/scenarios` - List scenarios
- `POST /api/v1/simulation/run` - Run simulation
- `GET /api/v1/simulation/fleet` - Fleet info

### Customer Management (NEW)
- `GET /api/v1/customers` - List customers
- `GET /api/v1/customers/{id}/analytics` - Customer insights
- `GET /api/v1/customers/stats/summary` - Overall stats

### Audit Trail (NEW)
- `GET /api/v1/audit-logs` - List audit logs
- `GET /api/v1/audit-logs/customer/{id}/timeline` - Customer timeline
- `GET /api/v1/audit-logs/stats/summary` - Audit stats

**Full API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)

---

## 🧪 Testing

### Automated Tests
```bash
# Inside backend container
docker exec -it concord-backend bash
python -m pytest

# Run integration tests
python test_all_phases.py
python test_integration_phases_6_7_8.py
```

### Manual Testing Checklist
- [ ] Submit action request via API
- [ ] View decision in dashboard
- [ ] Run simulation scenario
- [ ] Check customer analytics
- [ ] View audit logs
- [ ] Test conflict detection (submit 3 rapid requests)

---

## 📁 Project Structure

```
concord/
├── backend/
│   ├── app/
│   │   ├── models/          # 11 database models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   │   ├── arbitration/ # Decision engines
│   │   │   └── simulation/  # Agent simulators
│   │   └── schemas/         # Pydantic models
│   ├── alembic/             # Database migrations
│   └── tests/               # Test files
├── frontend/
│   ├── src/
│   │   ├── app/dashboard/   # 8 dashboard pages
│   │   ├── components/      # React components
│   │   └── lib/             # API client
└── docker-compose.yml       # Docker setup
```

---

## 🎯 Decision Flow Example

**Scenario**: Marketing bot wants to send offer to customer who just received payment reminder.

```
1. Gateway receives request
   ✓ API key validated
   ✓ Request validated

2. Arbitration Engine starts
   ✓ Consent check: Customer allows marketing
   ✓ Frequency check: 2 messages in last hour
   ⚠️ Conflict detected: Recent payment recovery message

3. Conflict Resolution
   Conflict Type: RAPID_SUCCESSION
   Severity: HIGH
   Recommended Strategy: DELAY_CONFLICTING
   
4. Decision: DELAY by 24 hours
   Reason: Customer attention budget exceeded
   Score: 42/100

5. Execution: Queued for delayed delivery
   Scheduled: Tomorrow 10:00 AM
   Channel: EMAIL
```

---

## 🏆 Hackathon Highlights

### Innovation
✅ First-ever multi-agent conflict resolution system  
✅ Intelligent merge strategies (7 algorithms)  
✅ Realistic fleet simulation for testing  

### Technical Excellence
✅ Clean, scalable architecture  
✅ 50+ REST API endpoints  
✅ Full-stack implementation  
✅ Production-ready code  

### Completeness
✅ 9/9 planned phases complete  
✅ Comprehensive documentation  
✅ Professional UI/UX  
✅ Ready to deploy  

---

## 📚 Documentation

- `README.md` - This file
- `PROJECT_COMPLETE.md` - Detailed project summary
- `PHASE6_COMPLETE.md` - Conflict & merge documentation
- `PHASE7_COMPLETE.md` - Simulation documentation
- `PHASE8_COMPLETE.md` - Customer & audit documentation
- `FINAL_VERIFICATION.md` - Verification checklist

---

## 🤝 For Judges

### Quick Demo Script (5 minutes)

1. **Show Dashboard** (1 min)
   - Open http://localhost:3000
   - Navigate through pages
   - Show real-time stats

2. **Run Simulation** (2 min)
   - Go to Simulation page
   - Select "Conflicting Agents"
   - Run with 10 customers, 10x speed
   - Show results and conflict resolution

3. **Explain Conflict Resolution** (1 min)
   - Show how conflicts are detected
   - Explain 7 merge strategies
   - Demo merge recommendation API

4. **Show Customer Analytics** (1 min)
   - Navigate to Customers page
   - View customer details
   - Show 30-day activity breakdown

### Key Points to Highlight

1. **Unique Problem**: Multi-agent communication chaos
2. **Innovative Solution**: Real-time conflict detection & resolution
3. **Production Ready**: Complete system, not just a prototype
4. **Scalable Architecture**: Clean separation of concerns
5. **Great UX**: Professional dashboard with simulation tools

---

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart
```

### Frontend shows errors
```bash
# Rebuild frontend
docker-compose up -d --build frontend
```

### Database issues
```bash
# Run migrations
docker exec -it concord-backend alembic upgrade head
```

### Port conflicts
Edit `docker-compose.yml` to use different ports if 3000/8000/5432/6379 are taken.

---

## 📝 License

MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

Built for **Razorpay AI Buildathon 2026**

**Tech Stack:**
- FastAPI, PostgreSQL, Redis
- Next.js, React, TypeScript
- Docker, SQLAlchemy, Pydantic
- Tailwind CSS, Lucide Icons

---

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**⭐ If you find this project interesting, please star it on GitHub! ⭐**

---

_Built with ❤️ for intelligent agent orchestration_
