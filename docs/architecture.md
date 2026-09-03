# CONCORD Architecture

## System Overview

CONCORD is a customer-level control plane for autonomous AI agent fleets. It sits between multiple specialized AI agents and customers, coordinating agent actions to ensure coherent, policy-compliant customer experiences.

## Core Principle

**Individual agents decide WHAT THEY WANT TO DO.**  
**Concord decides WHETHER, WHEN, AND HOW THEY SHOULD ACT.**

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI AGENT FLEET                            │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Cart   │  │ Payment  │  │  Upsell  │  │Subscription│      │
│  │ Recovery │  │ Recovery │  │  Agent   │  │  Agent    │       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬─────┘      │
│        │              │              │              │            │
└────────┼──────────────┼──────────────┼──────────────┼───────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                         ↓
         ┌───────────────────────────────────────┐
         │      CONCORD AGENT GATEWAY            │
         │  • Authentication                     │
         │  • Validation                         │
         │  • Idempotency                        │
         │  • Rate Limiting                      │
         └───────────────┬───────────────────────┘
                         ↓
         ┌───────────────────────────────────────┐
         │      CONCORD ARBITRATION ENGINE       │
         │                                        │
         │  ┌────────────────────────────────┐  │
         │  │  Customer State Engine         │  │
         │  │  • Identity Resolution         │  │
         │  │  • Consent                     │  │
         │  │  • Communication History       │  │
         │  │  • Attention Budget            │  │
         │  └────────────────────────────────┘  │
         │                                        │
         │  ┌────────────────────────────────┐  │
         │  │  Policy Engine (Deterministic) │  │
         │  │  • Priority Rules               │  │
         │  │  • Business Value Scoring      │  │
         │  │  • Frequency Limits            │  │
         │  │  • Offer Validation            │  │
         │  │  • Agent Permissions           │  │
         │  └────────────────────────────────┘  │
         │                                        │
         │  ┌────────────────────────────────┐  │
         │  │  AI Layer (Advisory)           │  │
         │  │  • Semantic Conflict Detection │  │
         │  │  • Intent Classification       │  │
         │  │  • Message Merging             │  │
         │  │  • Explanation Generation      │  │
         │  └────────────────────────────────┘  │
         │                                        │
         │  ┌────────────────────────────────┐  │
         │  │  Decision Engine               │  │
         │  │  • ALLOW / BLOCK / DELAY       │  │
         │  │  • MERGE                        │  │
         │  │  • Explainable Reasoning       │  │
         │  └────────────────────────────────┘  │
         └───────────────┬───────────────────────┘
                         ↓
         ┌───────────────────────────────────────┐
         │      ACTION EXECUTOR                   │
         │  • Idempotent Execution               │
         │  • Channel Integration                │
         │  • Retry Logic                        │
         └───────────────┬───────────────────────┘
                         ↓
         ┌───────────────────────────────────────┐
         │          CUSTOMER                      │
         └───────────────────────────────────────┘
                         ↓
         ┌───────────────────────────────────────┐
         │      AUDIT TRAIL                       │
         │  • Complete Decision History          │
         │  • Policy Enforcement Log             │
         │  • Conflict Resolution Record         │
         └───────────────────────────────────────┘
```

---

## Key Components

### 1. Agent Gateway

**Responsibilities:**
- Authenticate agents via API keys
- Validate request schemas
- Enforce agent permissions
- Implement idempotency (via `request_id`)
- Rate limit requests
- Log all incoming requests
- Forward to Arbitration Engine

**Security:**
- Each agent has unique API key
- Permissions stored per agent
- Agent cannot perform unauthorized actions

### 2. Customer Identity Resolver

**Purpose:** Resolve multiple identifiers to canonical customer

Different agents may identify customers differently:
- Email
- Phone
- External customer ID
- Payment customer ID
- Subscription customer ID

The resolver creates/retrieves a single Concord customer entity.

### 3. Customer State Engine

**Maintains:**
- Consent settings (marketing, transactional, global opt-out)
- Communication history
- Contacts today/this week
- Last contact timestamp
- Active intents
- Active offers
- Pending actions
- Attention budget
- Customer context/value

**Critical for:**
- Frequency enforcement
- Consent validation
- Context-aware decisions

### 4. Policy Engine (Deterministic)

**Enforces:**

**a) Consent Policies**
- Global opt-out → BLOCK all non-exempt
- Marketing consent required
- Transactional consent required

**b) Frequency Policies**
- Daily contact limits
- Intent-specific limits
- Channel-specific limits
- Attention budget depletion

**c) Priority Rules**
- Payment Recovery: 100
- Subscription Recovery: 90
- Cart Recovery: 70
- Win-back: 40
- Upsell: 30
- Promotion: 10

**d) Business Value Scoring**
- Estimated recovery amount
- Urgency (HIGH/MEDIUM/LOW)
- Customer lifetime value
- Combined priority + value score

**e) Offer Validation**
- Maximum discount limits
- Offer eligibility
- Conflicting offers

**f) Agent Permissions**
- Can agent issue discounts?
- Can agent access customer data?
- Can agent perform refunds?

### 5. AI Layer (Advisory Only)

**LLM provides:**
- Semantic conflict detection
- Intent classification
- Natural language merge
- Explanation generation

**LLM does NOT:**
- Authorize financial actions
- Override policy rules
- Make final decisions
- Bypass permissions

**Failure Mode:**
If LLM unavailable, system continues with deterministic rules.

### 6. Conflict Detector

**Detects:**

**Hard Conflicts:**
- Competing discounts (10% vs 15%)
- Contradictory messages
- Mutually exclusive offers

**Soft Conflicts:**
- Competing priorities
- Redundant messages
- Sub-optimal combinations

**Compatible Actions:**
- Can be merged into single interaction
- Non-conflicting intents

### 7. Merge Engine

**Process:**
1. Identify compatible actions
2. Use LLM to generate merged message
3. **Validate merged message against policies**
4. Ensure no unauthorized offers introduced
5. Return MERGE decision with combined message

### 8. Decision Engine

**Inputs:**
- Agent request(s)
- Customer state
- Merchant policies
- Other pending requests

**Outputs:**
One of:
- **ALLOW** - Execute action
- **BLOCK** - Reject action (with reason)
- **DELAY** - Queue for later (with schedule)
- **MERGE** - Combine with other action(s)

**Every decision includes:**
- Decision type
- Reason code
- Human-readable reason
- Policy IDs that influenced decision
- Conflicting request IDs
- Evaluation duration

### 9. Delayed Action Worker

**Background process that:**
- Monitors scheduled actions
- Re-evaluates when due
- Customer state may have changed
- Ensures action still valid
- Executes or re-delays

### 10. Audit Trail

**Records:**
- Every agent request
- Every decision
- Every policy check
- Every conflict
- Every execution
- Complete timeline per customer

**Enables:**
- "Why was this blocked?"
- "Which agent caused this?"
- "What policy prevented this?"
- Complete accountability

---

## Data Flow

### Example: Cart Recovery vs Payment Recovery

**Scenario:**
Customer has:
- Abandoned cart (₹500)
- Failed payment (₹850)

**Step 1: Requests Arrive**
```
Cart Agent → request_cart_001
  intent: CART_RECOVERY
  estimated_value: 500
  urgency: MEDIUM
  offer: 10% discount
  
Payment Agent → request_payment_001
  intent: PAYMENT_RECOVERY
  estimated_value: 850
  urgency: HIGH
  offer: null
```

**Step 2: Gateway**
- Validates both requests
- Checks permissions (both authorized)
- Persists to database
- Forwards to Arbitration Engine

**Step 3: Customer State**
- Retrieve customer
- Contacts today: 2/3
- Consent: all granted
- No active offers

**Step 4: Policy Evaluation**

Cart Request:
- Priority score: 70
- Value score: 500
- Combined score: 70*0.6 + 500*0.4 = 242

Payment Request:
- Priority score: 100
- Value score: 850
- Combined score: 100*0.6 + 850*0.4 = 400

**Step 5: Conflict Detection**
- Both target same customer
- Customer at 2/3 contact limit
- Compatible intents (could merge)
- Payment has higher combined score

**Step 6: Decision**

Payment Request:
- Decision: ALLOW
- Reason: "Higher priority and business value. Critical payment recovery."

Cart Request:
- Decision: DELAY
- Reason: "Lower priority. Customer approaching contact limit. Delay 6 hours."
- Scheduled: +6 hours

**Step 7: Execution**
- Payment message sent
- Contact recorded
- Audit logged
- Cart request queued

**Step 8: Background Worker**
- After 6 hours, re-evaluates cart request
- If payment succeeded → cart request may be cancelled
- If payment failed → cart request may be ALLOWED

---

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - High-performance API framework
- **SQLAlchemy** - ORM for database
- **Pydantic** - Schema validation
- **PostgreSQL** - Primary database
- **Redis** - Caching, counters, locks
- **Alembic** - Database migrations

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Recharts** - Analytics visualization

### Infrastructure
- **Docker & Docker Compose** - Local development
- **Vercel** - Frontend deployment (recommended)
- **Railway/Render/Fly** - Backend deployment (recommended)

---

## Database Schema

See: [Complete schema in models](../backend/app/models/)

**Core Tables:**
- `merchants` - Business entities
- `agents` - AI agents
- `customers` - End customers
- `policies` - Merchant policies
- `agent_requests` - All action requests
- `decisions` - Arbitration outcomes
- `customer_contacts` - Communication history
- `delayed_actions` - Queued actions
- `audit_logs` - Complete audit trail

**Key Relationships:**
- Merchant → Agents, Customers, Policies
- Customer → Requests, Decisions, Contacts
- Request → Decision (1:1)
- Decision → Audit Logs

---

## Scalability Considerations

### Phase 1 (MVP)
- Single instance
- PostgreSQL
- Redis
- Handles 100s of requests/minute

### Phase 2 (Production)
- Horizontal scaling
- Load balancer
- Database replicas
- Redis cluster
- Background worker pool
- Handles 1000s of requests/minute

### Phase 3 (Enterprise)
- Multi-region
- Event streaming (Kafka)
- Microservices
- Advanced caching
- Handles 10,000s of requests/minute

---

## Security

### Authentication & Authorization
- API key per agent
- Permissions per agent
- Merchant-level isolation
- Role-based access (future)

### Data Protection
- Secrets in environment variables
- API keys hashed in database
- No sensitive data in logs
- Input validation on all endpoints

### Compliance
- Complete audit trail
- Policy enforcement logs
- Consent management
- GDPR-ready (deletions, exports)

---

## Monitoring & Observability

### Metrics
- Requests per second
- Decision latency
- Policy violation rate
- Conflict detection rate
- Merge success rate
- Execution success rate

### Alerts
- High error rate
- Policy bypass attempts
- Unusual request patterns
- System degradation

### Dashboards
- Fleet-level overview
- Per-agent metrics
- Per-customer timeline
- Policy effectiveness

---

## Future Enhancements

### Short-term
- Multi-channel execution
- Advanced scheduling
- A/B testing framework
- Merchant customizable weights

### Medium-term
- ML-powered value prediction
- Adaptive priority learning
- Customer preference learning
- Multi-merchant support

### Long-term
- Real-time agent negotiation
- Distributed arbitration
- Agent marketplace
- Industry-specific templates

---

## Summary

CONCORD solves the cross-agent coordination problem by:

1. **Centralizing** all agent action requests
2. **Evaluating** them against customer state and merchant policies
3. **Coordinating** decisions across the entire agent fleet
4. **Ensuring** policy compliance and optimal customer experience
5. **Explaining** every decision with complete transparency
6. **Measuring** the impact with baseline comparison

The result: Individual agents remain smart, but the **fleet becomes intelligent**.
