# Phase 3: Arbitration Engine Test Guide

## Overview
This document outlines comprehensive tests for CONCORD's arbitration engine - the core decision-making system that determines whether agent requests are ALLOWED, BLOCKED, or DELAYED.

## Test Flow
```
Agent Request → Gateway → Arbitration Engine → Decision (ALLOW/BLOCK/DELAY)
                              ↓
                    ┌─────────┴─────────┐
                    │  13-Step Process  │
                    ├───────────────────┤
                    │ 1. Load customer  │
                    │ 2. Load policy    │
                    │ 3. Check expiry   │
                    │ 4. Check consent  │
                    │ 5. Check channel  │
                    │ 6. Check intent   │
                    │ 7. Validate offer │
                    │ 8. Check frequency│
                    │ 9. Score priority │
                    │10. Score value    │
                    │11. Combine scores │
                    │12. Check threshold│
                    │13. Custom rules   │
                    └───────────────────┘
```

## Prerequisites
1. Backend running at `localhost:8000`
2. Database populated with test data:
   - Merchant
   - Agent with API key
   - Customer with consent settings

## Test Scenarios

### Scenario 1: ALLOW - High Priority Payment Recovery
**Expected:** ALLOW decision with high score

```bash
# Register agent first
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Payment Recovery Agent",
    "description": "Handles payment recovery",
    "permissions": ["messaging", "discounts"]
  }'

# Save the API key from response

# Submit high-priority payment recovery request
curl -X POST http://localhost:8000/api/v1/actions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{
    "request_id": "test-allow-001",
    "customer_id": "CUST001",
    "action": "SEND_MESSAGE",
    "intent": "PAYMENT_RECOVERY",
    "channel": "EMAIL",
    "priority": 95,
    "estimated_value": 500000,
    "urgency": "HIGH",
    "message": "Your payment failed. Please update your payment method.",
    "expires_at": "2026-09-04T23:59:59Z"
  }'

# Expected Response:
# {
#   "id": "...",
#   "request_id": "test-allow-001",
#   "status": "approved",
#   "decision": {
#     "decision": "ALLOW",
#     "final_score": 85+,
#     "priority_score": 90+,
#     "value_score": 80+,
#     "message": "Request approved - score XX.XX"
#   }
# }
```

### Scenario 2: BLOCK - Global Opt-Out
**Expected:** BLOCK decision due to consent

```bash
curl -X POST http://localhost:8000/api/v1/actions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{
    "request_id": "test-block-consent",
    "customer_id": "CUST_OPTED_OUT",
    "action": "SEND_MESSAGE",
    "intent": "PROMOTION",
    "channel": "EMAIL",
    "priority": 50,
    "estimated_value": 100000,
    "urgency": "LOW",
    "message": "Check out our special offer!"
  }'

# Expected Response:
# {
#   "status": "blocked",
#   "decision": {
#     "decision": "BLOCK",
#     "block_reason": "global_opt_out",
#     "message": "Customer has globally opted out of all communications"
#   }
# }
```

### Scenario 3: BLOCK - Daily Limit Exceeded
**Expected:** BLOCK decision due to frequency

```bash
# Send 4 requests in quick succession (daily limit is 3)
for i in {1..4}; do
  curl -X POST http://localhost:8000/api/v1/actions \
    -H "Content-Type: application/json" \
    -H "X-API-Key: <API_KEY>" \
    -d "{
      \"request_id\": \"test-freq-$i\",
      \"customer_id\": \"CUST002\",
      \"action\": \"SEND_MESSAGE\",
      \"intent\": \"PROMOTION\",
      \"channel\": \"EMAIL\",
      \"priority\": 50,
      \"estimated_value\": 50000,
      \"urgency\": \"MEDIUM\",
      \"message\": \"Test message $i\"
    }"
  echo ""
done

# Expected: First 3 requests ALLOWED/DELAYED, 4th request BLOCKED with:
# {
#   "decision": "BLOCK",
#   "block_reason": "daily_limit_exceeded",
#   "message": "Daily limit reached: 3/3 contacts today"
# }
```

### Scenario 4: BLOCK - Invalid Offer (Exceeds Policy)
**Expected:** BLOCK decision due to offer validation

```bash
curl -X POST http://localhost:8000/api/v1/actions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{
    "request_id": "test-block-offer",
    "customer_id": "CUST003",
    "action": "SEND_MESSAGE",
    "intent": "UPSELL",
    "channel": "EMAIL",
    "priority": 60,
    "estimated_value": 100000,
    "urgency": "MEDIUM",
    "offer": {
      "unit": "PERCENT",
      "value": 50,
      "description": "50% off (exceeds policy limit)"
    },
    "message": "Special 50% discount just for you!"
  }'

# Expected Response:
# {
#   "decision": "BLOCK",
#   "block_reason": "invalid_offer",
#   "message": "Offer validation failed: Discount percentage 50% exceeds policy limit 30%"
# }
```

### Scenario 5: DELAY - Low Combined Score
**Expected:** DELAY decision due to low priority+value score

```bash
curl -X POST http://localhost:8000/api/v1/actions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{
    "request_id": "test-delay-001",
    "customer_id": "CUST004",
    "action": "SEND_MESSAGE",
    "intent": "PROMOTION",
    "channel": "EMAIL",
    "priority": 30,
    "estimated_value": 10000,
    "urgency": "LOW",
    "message": "Check out our products!",
    "expires_at": "2026-12-31T23:59:59Z"
  }'

# Expected Response:
# {
#   "decision": "DELAY",
#   "delay_reason": "low_combined_score",
#   "final_score": 40-60,
#   "message": "Request delayed - score XX.XX below optimal threshold"
# }
```

### Scenario 6: Query Decision Details
**Expected:** Full decision breakdown

```bash
# Get decision by request ID
curl -X GET "http://localhost:8000/api/v1/decisions/request/<REQUEST_UUID>" \
  -H "X-API-Key: <API_KEY>"

# Expected Response:
# {
#   "id": "...",
#   "decision": "ALLOW",
#   "final_score": 78.5,
#   "customer_state": {
#     "contacts_today": 1,
#     "attention_budget_remaining": 80,
#     "marketing_consent": true,
#     "global_opt_out": false
#   },
#   "checks": {
#     "consent": {"passed": true},
#     "frequency": {"passed": true, "cost": 30},
#     "priority": {
#       "score": 82.0,
#       "breakdown": {
#         "base_score": 90,
#         "urgency_multiplier": 1.2,
#         ...
#       }
#     },
#     "business_value": {
#       "score": 73.0,
#       "breakdown": {
#         "value_score": 70,
#         "urgency_value_score": 84,
#         ...
#       }
#     }
#   },
#   "score_weights": {
#     "priority": 0.6,
#     "value": 0.4
#   }
# }
```

## Automated Test Script

A Python test script `test_arbitration_flow.py` is provided for automated testing.

### Run Tests
```bash
cd backend
python test_arbitration_flow.py
```

## Verification Checklist

- [ ] Agent registration works
- [ ] Customer creation works  
- [ ] High-priority requests get ALLOWED
- [ ] Global opt-out blocks all requests
- [ ] Daily frequency limits are enforced
- [ ] Attention budget is calculated correctly
- [ ] Invalid offers are blocked
- [ ] Low-score requests get DELAYED
- [ ] Decision details endpoint returns full breakdown
- [ ] Scores are calculated correctly (priority 60%, value 40%)
- [ ] Idempotency works (duplicate request_id returns same decision)
- [ ] Audit logs are created for decisions

## Score Calculation Verification

### Priority Score (60% weight)
- Base score from intent: 40%
- Urgency multiplier: 20%
- Expiry pressure: 20%
- Customer engagement: 10%
- Intent uniqueness: 10%

### Business Value Score (40% weight)
- Estimated value: 50%
- Urgency-adjusted value: 20%
- Intent value multiplier: 15%
- Customer LTV proxy: 10%
- Offer ROI: 5%

### Final Score
```
final_score = (priority_score * 0.6) + (value_score * 0.4)
```

## Next Steps
After Phase 3 is complete and tested:
1. Phase 4: Real-time execution layer
2. Phase 5: Frontend dashboard
3. Phase 6: Analytics & reporting

## Status: ✅ PHASE 3 COMPLETE
