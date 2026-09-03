# Testing the CONCORD Agent Gateway

## Prerequisites

- Backend running: `docker-compose up -d backend`
- API available at: http://localhost:8000

## Step 1: Register an Agent

First, we need to create an agent and get an API key:

```bash
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cart Recovery Agent",
    "agent_type": "cart_recovery",
    "description": "Handles abandoned cart recovery",
    "permissions": {
      "messaging": true,
      "discounts": true,
      "high_value_discounts": false,
      "refunds": false
    }
  }'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Cart Recovery Agent",
  "agent_type": "cart_recovery",
  "api_key": "sk_live_abc123xyz789...",
  "permissions": {
    "messaging": true,
    "discounts": true,
    "high_value_discounts": false,
    "refunds": false
  },
  "is_active": true,
  "created_at": "2026-09-03T10:00:00Z"
}
```

**⚠️ SAVE THE API KEY!** It won't be shown again.

## Step 2: Create a Customer

Before submitting action requests, we need a customer. For now, let's create one directly in the database:

```bash
docker-compose exec -T postgres psql -U concord -d concord << 'EOF'
-- Get merchant ID
DO $$
DECLARE
    merchant_uuid UUID;
BEGIN
    SELECT id INTO merchant_uuid FROM merchants LIMIT 1;
    
    -- Insert customer
    INSERT INTO customers (id, merchant_id, external_id, name, email, phone, consent, custom_metadata, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        merchant_uuid,
        'cust_456',
        'Rahul Sharma',
        'rahul@example.com',
        '+91XXXXXXXXXX',
        '{"marketing": true, "transactional": true, "global_opt_out": false}'::jsonb,
        '{}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT DO NOTHING;
END $$;

-- Verify
SELECT external_id, name, email FROM customers WHERE external_id = 'cust_456';
EOF
```

## Step 3: Submit an Action Request

Now submit an action request using the agent's API key:

```bash
# Replace YOUR_API_KEY with the actual API key from Step 1
API_KEY="sk_live_YOUR_API_KEY_HERE"

curl -X POST "http://localhost:8000/api/v1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "request_id": "req_cart_20260903_001",
    "customer_id": "cust_456",
    "action": "SEND_MESSAGE",
    "intent": "CART_RECOVERY",
    "channel": "WHATSAPP",
    "priority": 70,
    "estimated_value": 85000,
    "urgency": "MEDIUM",
    "offer": {
      "type": "DISCOUNT",
      "value": 10,
      "unit": "PERCENT"
    },
    "message": "Complete your purchase and get 10% off!",
    "expires_at": "2026-09-03T18:00:00Z"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "request_id": "req_cart_20260903_001",
  "status": "pending",
  "message": "Request received and queued for arbitration",
  "created_at": "2026-09-03T10:41:02Z"
}
```

## Step 4: Test Idempotency

Submit the SAME request again (same request_id):

```bash
curl -X POST "http://localhost:8000/api/v1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "request_id": "req_cart_20260903_001",
    "customer_id": "cust_456",
    "action": "SEND_MESSAGE",
    "intent": "CART_RECOVERY",
    "channel": "WHATSAPP",
    "priority": 70,
    "estimated_value": 85000,
    "urgency": "MEDIUM",
    "offer": {
      "type": "DISCOUNT",
      "value": 10,
      "unit": "PERCENT"
    },
    "message": "Complete your purchase and get 10% off!",
    "expires_at": "2026-09-03T18:00:00Z"
  }'
```

**Expected Response (200 OK - Idempotent):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "request_id": "req_cart_20260903_001",
  "status": "pending",
  "message": "Duplicate request (idempotent)",
  "created_at": "2026-09-03T10:41:02Z"
}
```

Notice: Same ID, status code 200 instead of 201.

## Step 5: List Action Requests

```bash
curl -X GET "http://localhost:8000/api/v1/actions" \
  -H "Authorization: Bearer $API_KEY"
```

**Expected Response:**
```json
{
  "requests": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "request_id": "req_cart_20260903_001",
      "customer_id": "550e8400-e29b-41d4-a716-446655440002",
      "agent_id": "550e8400-e29b-41d4-a716-446655440000",
      "intent": "CART_RECOVERY",
      "channel": "WHATSAPP",
      "status": "pending",
      "created_at": "2026-09-03T10:41:02Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Step 6: Get Request Details

```bash
# Replace REQUEST_UUID with actual UUID from list response
REQUEST_UUID="550e8400-e29b-41d4-a716-446655440001"

curl -X GET "http://localhost:8000/api/v1/actions/$REQUEST_UUID" \
  -H "Authorization: Bearer $API_KEY"
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "request_id": "req_cart_20260903_001",
  "customer_id": "550e8400-e29b-41d4-a716-446655440002",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "merchant_id": "550e8400-e29b-41d4-a716-446655440003",
  "action_type": "SEND_MESSAGE",
  "intent": "CART_RECOVERY",
  "channel": "WHATSAPP",
  "priority": 70,
  "estimated_value": 85000,
  "urgency": "MEDIUM",
  "offer": {
    "type": "DISCOUNT",
    "value": 10,
    "unit": "PERCENT"
  },
  "message": "Complete your purchase and get 10% off!",
  "expires_at": "2026-09-03T18:00:00Z",
  "custom_metadata": {},
  "status": "pending",
  "created_at": "2026-09-03T10:41:02Z"
}
```

## Test Error Cases

### Test 1: Invalid API Key

```bash
curl -X POST "http://localhost:8000/api/v1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_live_invalid_key" \
  -d '{
    "request_id": "req_test_001",
    "customer_id": "cust_456",
    "action": "SEND_MESSAGE",
    "intent": "CART_RECOVERY",
    "channel": "WHATSAPP",
    "priority": 70,
    "message": "Test message"
  }'
```

**Expected: 401 Unauthorized**

### Test 2: Permission Denied (High Value Discount)

```bash
# Agent doesn't have high_value_discounts permission
curl -X POST "http://localhost:8000/api/v1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "request_id": "req_test_002",
    "customer_id": "cust_456",
    "action": "SEND_MESSAGE",
    "intent": "CART_RECOVERY",
    "channel": "WHATSAPP",
    "priority": 70,
    "offer": {
      "type": "DISCOUNT",
      "value": 20,
      "unit": "PERCENT"
    },
    "message": "Get 20% off!",
    "expires_at": "2026-09-03T18:00:00Z"
  }'
```

**Expected: 400 Bad Request - PERMISSION_DENIED**

### Test 3: Customer Not Found

```bash
curl -X POST "http://localhost:8000/api/v1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "request_id": "req_test_003",
    "customer_id": "cust_nonexistent",
    "action": "SEND_MESSAGE",
    "intent": "CART_RECOVERY",
    "channel": "WHATSAPP",
    "priority": 70,
    "message": "Test message"
  }'
```

**Expected: 400 Bad Request - CUSTOMER_NOT_FOUND**

### Test 4: Invalid Request (Missing Required Field)

```bash
curl -X POST "http://localhost:8000/api/v1/actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "request_id": "req_test_004",
    "customer_id": "cust_456",
    "action": "SEND_MESSAGE",
    "intent": "CART_RECOVERY"
  }'
```

**Expected: 422 Validation Error (missing channel, priority, message)**

## Verify in Database

Check the database to see persisted requests:

```bash
docker-compose exec -T postgres psql -U concord -d concord << 'EOF'
SELECT 
    request_id,
    intent,
    channel,
    priority,
    estimated_value,
    urgency,
    status,
    created_at
FROM agent_requests
ORDER BY created_at DESC
LIMIT 5;
EOF
```

Check audit logs:

```bash
docker-compose exec -T postgres psql -U concord -d concord << 'EOF'
SELECT 
    entity_type,
    action,
    details->>'request_id' as request_id,
    details->>'intent' as intent,
    created_at
FROM audit_logs
ORDER BY created_at DESC
LIMIT 5;
EOF
```

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI where you can:
- Try out all endpoints
- See request/response schemas
- Test authentication
- View detailed API documentation

## Success Criteria

✅ Agent registration works  
✅ API key authentication works  
✅ Action request submission works  
✅ Idempotency works (duplicate requests return 200)  
✅ Permission validation works  
✅ Offer validation works  
✅ Customer resolution works  
✅ Requests persisted to database  
✅ Audit logs created  
✅ List and detail endpoints work  
✅ Error responses are structured and helpful  

## Next Steps

Once the gateway is working:
1. Phase 3: Build the Arbitration Engine
2. Add decision-making logic
3. Implement ALLOW/BLOCK/DELAY/MERGE decisions
4. Add policy enforcement
5. Build simulation system
