# CONCORD API Documentation

Base URL: `http://localhost:8000` (development)

---

## Authentication

All agent requests require API key authentication.

```
Authorization: Bearer <agent_api_key>
```

---

## Agent Actions

### Submit Action Request

Submit an agent action request for arbitration.

**Endpoint:** `POST /api/v1/actions`

**Request Body:**
```json
{
  "request_id": "req_cart_20260903_001",
  "customer_id": "cust_456",
  "agent_id": "agent_cart_recovery",
  "action": "SEND_MESSAGE",
  "intent": "CART_RECOVERY",
  "channel": "WHATSAPP",
  "priority": 70,
  "estimated_value": 850,
  "urgency": "MEDIUM",
  "offer": {
    "type": "DISCOUNT",
    "value": 10,
    "unit": "PERCENT"
  },
  "message": "Complete your purchase and get 10% off.",
  "expires_at": "2026-09-03T18:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "request_id": "req_cart_20260903_001",
  "status": "pending",
  "created_at": "2026-09-03T10:41:02Z"
}
```

**Errors:**
- `400` - Invalid request schema
- `401` - Authentication failed
- `403` - Agent not authorized for this action
- `409` - Duplicate request_id

---

### List Action Requests

**Endpoint:** `GET /api/v1/actions`

**Query Parameters:**
- `customer_id` - Filter by customer
- `agent_id` - Filter by agent
- `status` - Filter by status (pending, evaluated, expired)
- `limit` - Results per page (default: 50)
- `offset` - Pagination offset

**Response:** `200 OK`
```json
{
  "requests": [...],
  "total": 127,
  "limit": 50,
  "offset": 0
}
```

---

### Get Action Request

**Endpoint:** `GET /api/v1/actions/{request_id}`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "request_id": "req_cart_20260903_001",
  "customer_id": "cust_456",
  "agent_id": "agent_cart_recovery",
  "action": "SEND_MESSAGE",
  "intent": "CART_RECOVERY",
  "status": "evaluated",
  "created_at": "2026-09-03T10:41:02Z",
  "decision": {
    "decision": "DELAY",
    "reason": "Customer at contact limit",
    "scheduled_at": "2026-09-03T16:00:00Z"
  }
}
```

---

## Decisions

### List Decisions

**Endpoint:** `GET /api/v1/decisions`

**Query Parameters:**
- `customer_id` - Filter by customer
- `decision` - Filter by decision type (ALLOW, BLOCK, DELAY, MERGE)
- `limit` - Results per page
- `offset` - Pagination offset

**Response:** `200 OK`
```json
{
  "decisions": [
    {
      "id": "uuid",
      "request_id": "uuid",
      "decision": "ALLOW",
      "reason_code": "POLICY_COMPLIANT",
      "reason": "Request meets all policy requirements",
      "created_at": "2026-09-03T10:41:03Z"
    }
  ],
  "total": 89,
  "limit": 50,
  "offset": 0
}
```

---

### Get Decision Details

**Endpoint:** `GET /api/v1/decisions/{decision_id}`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "request_id": "uuid",
  "customer_id": "uuid",
  "decision": "BLOCK",
  "reason_code": "FREQUENCY_LIMIT_EXCEEDED",
  "reason": "Customer has reached daily contact limit of 3",
  "policy_ids": ["policy_frequency_001"],
  "conflicting_requests": [],
  "evaluation_duration_ms": 23,
  "created_at": "2026-09-03T10:41:03Z"
}
```

---

## Customers

### List Customers

**Endpoint:** `GET /api/v1/customers`

**Query Parameters:**
- `limit` - Results per page
- `offset` - Pagination offset

**Response:** `200 OK`
```json
{
  "customers": [
    {
      "id": "uuid",
      "external_id": "cust_456",
      "name": "Rahul Sharma",
      "email": "rahul@example.com",
      "consent": {
        "marketing": true,
        "transactional": true,
        "global_opt_out": false
      },
      "created_at": "2026-09-01T00:00:00Z"
    }
  ],
  "total": 250,
  "limit": 50,
  "offset": 0
}
```

---

### Get Customer Details

**Endpoint:** `GET /api/v1/customers/{customer_id}`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "external_id": "cust_456",
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone": "+91XXXXXXXXXX",
  "consent": {
    "marketing": true,
    "transactional": true,
    "global_opt_out": false
  },
  "state": {
    "contacts_today": 2,
    "daily_limit": 3,
    "last_contact": "2026-09-03T09:15:00Z",
    "attention_budget_remaining": 60,
    "active_intents": ["PAYMENT_RECOVERY", "CART_ABANDONMENT"],
    "active_offers": [
      {
        "type": "DISCOUNT",
        "value": 10,
        "unit": "PERCENT"
      }
    ]
  },
  "recent_decisions": [...],
  "created_at": "2026-09-01T00:00:00Z"
}
```

---

## Agents

### List Agents

**Endpoint:** `GET /api/v1/agents`

**Response:** `200 OK`
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "Cart Recovery Agent",
      "agent_type": "cart_recovery",
      "is_active": true,
      "permissions": {
        "messaging": true,
        "discounts": true,
        "refunds": false
      },
      "created_at": "2026-09-01T00:00:00Z"
    }
  ]
}
```

---

### Register Agent

**Endpoint:** `POST /api/v1/agents`

**Request Body:**
```json
{
  "name": "Cart Recovery Agent",
  "agent_type": "cart_recovery",
  "description": "Handles abandoned cart recovery",
  "permissions": {
    "messaging": true,
    "discounts": true,
    "high_value_discounts": false,
    "refunds": false
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "Cart Recovery Agent",
  "api_key": "sk_live_...",
  "created_at": "2026-09-03T10:41:03Z"
}
```

---

## Policies

### Get Policies

**Endpoint:** `GET /api/v1/policies`

**Response:** `200 OK`
```json
{
  "policies": [
    {
      "id": "uuid",
      "policy_type": "frequency",
      "name": "Daily Contact Limit",
      "config": {
        "max_daily_contacts": 3,
        "intent_specific": {
          "marketing": 2,
          "transactional": 5
        }
      },
      "is_active": true
    },
    {
      "id": "uuid",
      "policy_type": "discount",
      "name": "Maximum Discount",
      "config": {
        "max_discount_percent": 10,
        "max_discount_amount": 100000
      },
      "is_active": true
    },
    {
      "id": "uuid",
      "policy_type": "priority",
      "name": "Agent Priorities",
      "config": {
        "payment_recovery": 100,
        "subscription_recovery": 90,
        "cart_recovery": 70,
        "win_back": 40,
        "upsell": 30,
        "promotion": 10
      },
      "is_active": true
    }
  ]
}
```

---

### Update Policies

**Endpoint:** `PUT /api/v1/policies`

**Request Body:**
```json
{
  "frequency": {
    "max_daily_contacts": 5
  },
  "discount": {
    "max_discount_percent": 15
  },
  "priority": {
    "payment_recovery": 100,
    "cart_recovery": 80
  }
}
```

**Response:** `200 OK`

---

## Audit

### Get Customer Audit Timeline

**Endpoint:** `GET /api/v1/audit/{customer_id}`

**Query Parameters:**
- `limit` - Results per page
- `offset` - Pagination offset

**Response:** `200 OK`
```json
{
  "customer_id": "uuid",
  "timeline": [
    {
      "timestamp": "2026-09-03T10:41:02Z",
      "event": "AGENT_REQUEST",
      "agent": "Cart Recovery Agent",
      "action": "SEND_MESSAGE",
      "intent": "CART_RECOVERY"
    },
    {
      "timestamp": "2026-09-03T10:41:03Z",
      "event": "DECISION",
      "decision": "DELAY",
      "reason": "Customer at contact limit"
    }
  ]
}
```

---

## Simulation

### Run Fleet Simulation

**Endpoint:** `POST /api/v1/simulation/run`

**Request Body:**
```json
{
  "num_customers": 100,
  "num_requests": 1000,
  "agents": ["cart_recovery", "payment_recovery", "upsell", "subscription"],
  "scenarios": ["conflicting_discounts", "frequency_exceeded", "concurrent_requests"],
  "baseline_mode": false
}
```

**Response:** `200 OK`
```json
{
  "simulation_id": "uuid",
  "status": "completed",
  "metrics": {
    "total_requests": 1000,
    "allowed": 450,
    "blocked": 320,
    "delayed": 180,
    "merged": 50,
    "conflicts_detected": 127,
    "policy_violations_prevented": 89,
    "duplicate_contacts_prevented": 45,
    "avg_decision_latency_ms": 18
  },
  "baseline_comparison": {
    "baseline_contacts": 780,
    "concord_contacts": 450,
    "improvement_percent": 42
  },
  "duration_ms": 2341
}
```

---

## Analytics

### Get Dashboard Overview

**Endpoint:** `GET /api/v1/analytics/overview`

**Query Parameters:**
- `start_date` - Filter from date
- `end_date` - Filter to date

**Response:** `200 OK`
```json
{
  "period": {
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-09-03T23:59:59Z"
  },
  "metrics": {
    "total_requests": 1547,
    "allowed": 789,
    "blocked": 512,
    "delayed": 201,
    "merged": 45,
    "conflicts_detected": 234,
    "policy_violations_prevented": 156,
    "avg_decision_latency_ms": 21,
    "customer_contacts": 789,
    "unique_customers": 250
  },
  "by_agent": {
    "cart_recovery": {
      "requests": 450,
      "allowed": 290,
      "blocked": 120,
      "delayed": 40
    },
    "payment_recovery": {
      "requests": 380,
      "allowed": 350,
      "blocked": 20,
      "delayed": 10
    }
  },
  "by_decision": {
    "ALLOW": 789,
    "BLOCK": 512,
    "DELAY": 201,
    "MERGE": 45
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "request_id": "req_123",
    "timestamp": "2026-09-03T10:41:03Z"
  }
}
```

**Common Error Codes:**
- `INVALID_REQUEST` - Malformed request
- `AUTHENTICATION_FAILED` - Invalid API key
- `AGENT_NOT_AUTHORIZED` - Agent lacks permission
- `POLICY_VIOLATION` - Request violates policy
- `CUSTOMER_NOT_FOUND` - Customer doesn't exist
- `DUPLICATE_REQUEST` - request_id already exists
- `INTERNAL_SERVER_ERROR` - System error

---

## Rate Limiting

- **Agent requests:** 100 requests/minute per agent
- **Dashboard API:** 1000 requests/minute per merchant

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1693737603
```

---

## Webhooks (Future)

Concord will support webhooks for real-time notifications:

- `decision.created` - New arbitration decision
- `action.executed` - Action successfully executed
- `conflict.detected` - Agent conflict detected
- `policy.violated` - Policy violation attempt

---

## SDK Support (Future)

Official SDKs planned for:
- Python
- Node.js
- Java
- Go

---

## Versioning

API version is included in the URL: `/api/v1/`

Breaking changes will increment the version number.
