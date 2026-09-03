# Updated Specification - Changes & Implementation Plan

## Executive Summary

The updated prompt adds **critical new requirements** around business value, customer identity resolution, baseline comparison, and failure injection testing. It also reinforces the positioning as a "cross-agent arbitration layer" rather than just frequency management.

---

## ✅ What We've Already Built (Aligned)

### Phase 1 Complete ✓
- [x] Project structure (monorepo with backend/frontend/docs)
- [x] FastAPI backend with proper configuration
- [x] PostgreSQL database models (9 entities)
- [x] Docker Compose setup
- [x] Requirements and dependencies
- [x] Proper gitignore and README
- [x] Agent request schema matches spec
- [x] Decision schema matches spec
- [x] Audit trail architecture
- [x] Delayed action support
- [x] JSONB for flexible policies
- [x] UUIDs for all entities
- [x] Proper indexes for queries
- [x] Idempotency support (request_id)

---

## 🆕 New Requirements from Updated Spec

### 1. **Business Value Engine** ⭐ CRITICAL

**What Changed:**
- Original spec: Priority-based arbitration only
- Updated spec: Priority + Business value estimation

**New Fields Required:**
- `estimated_value` - Expected recovery/revenue (₹)
- `urgency` - HIGH/MEDIUM/LOW

**Implementation Impact:**
```python
# Arbitration must now consider:
decision = evaluate(
    rule_based_priority=70,      # Cart recovery
    estimated_value=850,          # ₹850 recovery
    urgency="HIGH",               # Time-sensitive
    merchant_weights=config
)
```

**Status:** ✅ Model updated with new fields

---

### 2. **Customer Identity Resolver** 🆕

**What's New:**
Different agents may identify customers differently:
- Agent A: uses email
- Agent B: uses phone  
- Agent C: uses payment_customer_id
- Agent D: uses subscription_customer_id

**Required Component:**
```python
class CustomerIdentityResolver:
    def resolve(
        self,
        merchant_id: str,
        identifiers: Dict[str, str]
    ) -> Customer:
        """
        Resolve multiple identifiers to canonical customer
        """
```

**Implementation:**
- Add to `app/services/customer_identity.py`
- Support email, phone, external_id, payment_id, subscription_id
- Return canonical Concord customer_id

**Status:** ⏳ Not yet implemented

---

### 3. **Attention Budget Concept** 🆕

**What Changed:**
- Original: Simple daily contact limit
- Updated: "Attention budget" - more sophisticated

**Implications:**
- Not just "3 contacts today"
- Consider: value of contact, customer tolerance, intent type, channel
- Budget depletes differently for different contact types

**Example:**
```
Customer attention budget: 100 points/day
- Payment recovery: 20 points
- Cart recovery: 30 points
- Upsell: 40 points
- Promotion: 50 points
```

**Status:** ⏳ Needs design & implementation

---

### 4. **Baseline vs Concord Comparison** ⭐ CRITICAL

**What's New:**
Simulation must show TWO modes:

**Mode 1: BASELINE (No Concord)**
- Agents act independently
- No coordination
- Measure: conflicts, duplicates, policy violations

**Mode 2: WITH CONCORD**
- Agents arbitrated through Concord
- Coordinated behavior
- Measure: improvements

**Dashboard Must Show:**
```
Baseline:
- 47 customer contacts
- 12 policy violations
- 8 conflicting offers
- ₹4,200 unnecessary discounts

With Concord:
- 31 customer contacts (-34%)
- 0 policy violations (-100%)
- 0 conflicting offers (-100%)
- ₹850 unnecessary discounts (-80%)
```

**Status:** ⏳ Not yet implemented

---

### 5. **Failure Injection Testing** 🆕

**Required Test Scenarios:**

```python
def test_concurrent_duplicate_requests():
    """10 identical requests arrive simultaneously"""
    # Only 1 should execute
    
def test_llm_unavailable():
    """LLM fails, deterministic engine continues"""
    
def test_database_timeout():
    """DB slow, system fails safely"""
    
def test_conflicting_concurrent_agents():
    """5 agents request same customer simultaneously"""
    # Deterministic outcome despite race condition
    
def test_stale_delayed_action():
    """Delayed action fires but customer state changed"""
    # Re-evaluation prevents bad action
```

**Status:** ⏳ Not yet implemented

---

### 6. **Enhanced Positioning Requirements**

**Critical Messaging:**

❌ **DO NOT SAY:**
- "Anti-spam system"
- "Frequency limiter"
- "Notification manager"
- "Razorpay has no agent guardrails"

✅ **DO SAY:**
- "Cross-agent arbitration and governance layer"
- "Complements agent-level guardrails"
- "Solves emergent cross-agent behavior"
- "Fleet-level intelligence"

**Status:** ✅ README already reflects this

---

### 7. **Priority vs Business Value Arbitration**

**Two-Dimensional Evaluation:**

```python
class ArbitrationEngine:
    def evaluate(self, requests: List[AgentRequest]):
        # Dimension 1: Rule-based priority
        priority_score = get_priority(request.intent)
        
        # Dimension 2: Business value
        value_score = calculate_value(
            estimated_value=request.estimated_value,
            urgency=request.urgency,
            customer_context=customer.context
        )
        
        # Combined scoring
        final_score = (
            priority_score * merchant.priority_weight +
            value_score * merchant.value_weight
        )
```

**Status:** ⏳ Needs implementation in arbitration engine

---

## 📋 Updated Implementation Plan

### Current Status: Phase 1 Complete ✓

### Phase 1: Foundation ✅ DONE
- [x] Project structure
- [x] Database models (with business value fields)
- [x] Docker setup
- [x] Configuration

### Phase 2: Model Updates & Migrations ⏳ IN PROGRESS
- [x] Add estimated_value and urgency to AgentRequest
- [ ] Set up Alembic migrations
- [ ] Create initial migration
- [ ] Test database creation

### Phase 3: Agent Gateway
- [ ] Action request API
- [ ] Authentication
- [ ] Validation (with business value)
- [ ] Idempotency
- [ ] Persistence

### Phase 4: Customer Identity Resolver 🆕
- [ ] Identity resolution service
- [ ] Multi-identifier support
- [ ] Canonical customer ID mapping

### Phase 5: Core Arbitration Engine
- [ ] Customer state engine
- [ ] Consent engine
- [ ] Frequency/attention budget engine 🆕
- [ ] Policy engine
- [ ] Priority engine
- [ ] **Business value engine** 🆕
- [ ] Combined priority + value scoring 🆕
- [ ] ALLOW/BLOCK/DELAY decisions

### Phase 6: Cross-Agent Intelligence
- [ ] Conflict detector
- [ ] Merge engine (with LLM)
- [ ] Merge validation
- [ ] Delayed action worker

### Phase 7: Audit & Analytics
- [ ] Complete audit trail
- [ ] Decision explanations
- [ ] Metrics calculation
- [ ] **Baseline metrics** 🆕

### Phase 8: Simulation Engine 🆕 ENHANCED
- [ ] Synthetic agents (5+)
- [ ] Synthetic customers (100+)
- [ ] **Baseline mode (no Concord)** 🆕
- [ ] Concord mode (with arbitration)
- [ ] Concurrent request simulation
- [ ] **Comparison metrics** 🆕
- [ ] **Failure injection** 🆕

### Phase 9: Frontend Dashboard
- [ ] Overview dashboard
- [ ] **Baseline vs Concord comparison view** 🆕
- [ ] Agents page
- [ ] Customer detail page
- [ ] Policy editor
- [ ] Simulation interface
- [ ] Audit timeline

### Phase 10: AI Layer
- [ ] LLM provider abstraction
- [ ] Semantic conflict detection
- [ ] Message merging
- [ ] Intent classification
- [ ] Explanation generation

### Phase 11: Testing & Hardening 🆕
- [ ] Concurrent request tests
- [ ] **Failure injection tests** 🆕
- [ ] LLM unavailable handling
- [ ] Database failure handling
- [ ] Duplicate webhook handling
- [ ] Race condition testing

### Phase 12: Deployment & Polish
- [ ] Deployment configuration
- [ ] Architecture diagram
- [ ] Demo preparation
- [ ] Performance testing
- [ ] Security review

---

## 🎯 Immediate Next Steps

**Recommendation: Continue Phase 2 - Complete Foundation**

1. **Task 4: Set up Alembic** ⏳ BLOCKED (was in progress)
   - Create alembic.ini
   - Initialize Alembic
   - Create initial migration with all models
   - Test migration up/down

2. **Task 5: Verify Configuration**
   - Ensure business value fields are in config defaults
   - Add attention budget config
   - Add value/priority weight configs

3. **Task 6: Frontend Scaffolding**
   - Initialize Next.js project
   - Basic structure only
   - Don't build UI yet

4. **Task 7: Documentation**
   - Architecture diagram
   - API documentation outline
   - Product spec document

---

## 🔴 Critical Gaps to Address

### Priority 1: Business Value Engine
**Why Critical:** Core differentiation of updated spec
**When:** Phase 5 (Arbitration Engine)
**Dependencies:** Models updated ✓, Config ready

### Priority 2: Baseline Comparison
**Why Critical:** Required for demo impact measurement
**When:** Phase 8 (Simulation)
**Dependencies:** Arbitration engine complete, Simulation engine

### Priority 3: Failure Injection
**Why Critical:** Demonstrates production-quality engineering
**When:** Phase 11 (Testing)
**Dependencies:** Core system working

### Priority 4: Attention Budget
**Why Critical:** More sophisticated than simple frequency limit
**When:** Phase 5 (Arbitration Engine)
**Dependencies:** Customer state engine

---

## ✅ Approval Request

**Proposed Next Action:**
Continue with **Phase 2: Complete Foundation**
- Set up Alembic migrations
- Test database creation
- Verify all models work

Then proceed to **Phase 3: Agent Gateway** to get the API working.

**Rationale:**
- Foundation (Phase 1) is 90% complete
- Need working database before building services
- Agent Gateway is the entry point - build it next
- Then we can build arbitration engine with business value support

**Should I proceed with completing Phase 2 (Alembic setup)?**
