"""
Automated Test Script for Phase 3: Arbitration Engine
Tests the complete flow: request → gateway → arbitration → decision
"""

import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = None  # Will be set after agent registration


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(test_name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")


def setup_test_data():
    """Setup: Create merchant, agent, and customers"""
    print_section("SETUP: Creating Test Data")
    
    global API_KEY
    
    # Create agent
    print("1. Creating test agent...")
    response = requests.post(
        f"{BASE_URL}/agents",
        json={
            "name": "Test Arbitration Agent",
            "agent_type": "test_agent",
            "description": "Agent for testing arbitration engine",
            "permissions": {
                "messaging": True,
                "discounts": True,
                "high_value_discounts": True
            }
        }
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        API_KEY = data.get("api_key")
        print(f"   ✅ Agent created: {data.get('name')}")
        print(f"   API Key: {API_KEY[:20]}...")
        return True
    else:
        print(f"   ❌ Failed to create agent: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_allow_high_priority():
    """Test 1: High-priority payment recovery should be ALLOWED"""
    print_section("TEST 1: ALLOW - High Priority Payment Recovery")
    
    expires_at = (datetime.now() + timedelta(hours=6)).isoformat() + "Z"
    
    response = requests.post(
        f"{BASE_URL}/actions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "request_id": f"test-allow-{int(time.time())}",
            "customer_id": "CUST_TEST_001",
            "action": "SEND_MESSAGE",
            "intent": "PAYMENT_RECOVERY",
            "channel": "EMAIL",
            "priority": 95,
            "estimated_value": 500000,  # ₹5000
            "urgency": "HIGH",
            "message": "Your payment failed. Please update your payment method.",
            "expires_at": expires_at
        }
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        # Check if decision exists
        has_decision = "decision" in data
        decision_type = data.get("decision", {}).get("decision") if has_decision else None
        status = data.get("status")
        
        passed = status == "approved" or decision_type == "ALLOW"
        
        details = f"Status: {status}"
        if has_decision:
            details += f", Decision: {decision_type}"
            final_score = data.get("decision", {}).get("final_score")
            if final_score:
                details += f", Score: {final_score}"
        
        print_result("High priority request allowed", passed, details)
        return passed
    else:
        print(f"Error: {response.text}")
        print_result("High priority request allowed", False, f"HTTP {response.status_code}")
        return False


def test_block_invalid_offer():
    """Test 2: Offer exceeding policy limits should be BLOCKED"""
    print_section("TEST 2: BLOCK - Invalid Offer (Exceeds Policy)")
    
    response = requests.post(
        f"{BASE_URL}/actions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "request_id": f"test-block-offer-{int(time.time())}",
            "customer_id": "CUST_TEST_002",
            "action": "SEND_MESSAGE",
            "intent": "UPSELL",
            "channel": "EMAIL",
            "priority": 60,
            "estimated_value": 100000,
            "urgency": "MEDIUM",
            "offer": {
                "type": "DISCOUNT",
                "unit": "PERCENT",
                "value": 50,  # Exceeds 30% policy limit
                "description": "50% off - should be blocked"
            },
            "message": "Special 50% discount!"
        }
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        status = data.get("status")
        decision_type = data.get("decision", {}).get("decision")
        block_reason = data.get("decision", {}).get("block_reason")
        
        passed = status == "blocked" or (decision_type == "BLOCK" and block_reason == "invalid_offer")
        
        details = f"Status: {status}, Decision: {decision_type}, Reason: {block_reason}"
        print_result("Invalid offer blocked", passed, details)
        return passed
    else:
        print(f"Error: {response.text}")
        print_result("Invalid offer blocked", False, f"HTTP {response.status_code}")
        return False


def test_delay_low_score():
    """Test 3: Low-score request should be DELAYED"""
    print_section("TEST 3: DELAY - Low Combined Score")
    
    expires_at = (datetime.now() + timedelta(days=30)).isoformat() + "Z"
    
    response = requests.post(
        f"{BASE_URL}/actions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "request_id": f"test-delay-{int(time.time())}",
            "customer_id": "CUST_TEST_003",
            "action": "SEND_MESSAGE",
            "intent": "PROMOTION",
            "channel": "EMAIL",
            "priority": 25,
            "estimated_value": 5000,  # ₹50 - low value
            "urgency": "LOW",
            "message": "Check out our products!",
            "expires_at": expires_at
        }
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        status = data.get("status")
        decision_type = data.get("decision", {}).get("decision")
        final_score = data.get("decision", {}).get("final_score")
        
        passed = status == "delayed" or decision_type == "DELAY"
        
        details = f"Status: {status}, Decision: {decision_type}"
        if final_score:
            details += f", Score: {final_score}"
        
        print_result("Low score request delayed", passed, details)
        return passed
    else:
        print(f"Error: {response.text}")
        print_result("Low score request delayed", False, f"HTTP {response.status_code}")
        return False


def test_idempotency():
    """Test 4: Duplicate request_id should return same result"""
    print_section("TEST 4: Idempotency Check")
    
    request_id = f"test-idempotency-{int(time.time())}"
    
    request_data = {
        "request_id": request_id,
        "customer_id": "CUST_TEST_004",
        "action": "SEND_MESSAGE",
        "intent": "CART_RECOVERY",
        "channel": "EMAIL",
        "priority": 70,
        "estimated_value": 200000,
        "urgency": "HIGH",
        "message": "Complete your purchase!"
    }
    
    # First request
    print("Sending first request...")
    response1 = requests.post(
        f"{BASE_URL}/actions",
        headers={"X-API-Key": API_KEY},
        json=request_data
    )
    
    if response1.status_code not in [200, 201]:
        print_result("Idempotency check", False, f"First request failed: {response1.status_code}")
        return False
    
    data1 = response1.json()
    status1 = response1.status_code
    
    # Second request (duplicate)
    print("Sending duplicate request...")
    time.sleep(1)
    response2 = requests.post(
        f"{BASE_URL}/actions",
        headers={"X-API-Key": API_KEY},
        json=request_data
    )
    
    data2 = response2.json()
    status2 = response2.status_code
    
    # First should be 201, second should be 200
    passed = (status1 == 201 and status2 == 200) and (data1.get("id") == data2.get("id"))
    
    details = f"First: {status1}, Second: {status2}, Same ID: {data1.get('id') == data2.get('id')}"
    print_result("Idempotency works correctly", passed, details)
    return passed


def test_query_decision():
    """Test 5: Query decision details"""
    print_section("TEST 5: Query Decision Details")
    
    # First create a request
    response = requests.post(
        f"{BASE_URL}/actions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "request_id": f"test-query-{int(time.time())}",
            "customer_id": "CUST_TEST_005",
            "action": "SEND_MESSAGE",
            "intent": "SUBSCRIPTION_RECOVERY",
            "channel": "EMAIL",
            "priority": 85,
            "estimated_value": 300000,
            "urgency": "HIGH",
            "message": "Your subscription is expiring soon!"
        }
    )
    
    if response.status_code not in [200, 201]:
        print_result("Query decision details", False, "Failed to create request")
        return False
    
    data = response.json()
    request_id = data.get("id")
    
    print(f"Request created: {request_id}")
    
    # Query decision by request ID
    print("Querying decision details...")
    time.sleep(1)
    
    decision_response = requests.get(
        f"{BASE_URL}/decisions/request/{request_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    
    print(f"Decision Query Status: {decision_response.status_code}")
    
    if decision_response.status_code == 200:
        decision_data = decision_response.json()
        print(json.dumps(decision_data, indent=2))
        
        has_breakdown = "checks" in decision_data
        has_scores = "priority_score" in decision_data and "value_score" in decision_data
        
        passed = has_breakdown and has_scores
        details = f"Has checks: {has_breakdown}, Has scores: {has_scores}"
        print_result("Decision details retrieved", passed, details)
        return passed
    else:
        print(f"Error: {decision_response.text}")
        print_result("Decision details retrieved", False, f"HTTP {decision_response.status_code}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║    CONCORD PHASE 3: ARBITRATION ENGINE TEST SUITE         ║")
    print("║    Testing: request → gateway → arbitration → decision    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Setup
    if not setup_test_data():
        print("\n❌ Setup failed. Cannot continue with tests.")
        return
    
    time.sleep(2)  # Give backend time to process
    
    # Run tests
    results.append(("High Priority ALLOW", test_allow_high_priority()))
    time.sleep(1)
    
    results.append(("Invalid Offer BLOCK", test_block_invalid_offer()))
    time.sleep(1)
    
    results.append(("Low Score DELAY", test_delay_low_score()))
    time.sleep(1)
    
    results.append(("Idempotency", test_idempotency()))
    time.sleep(1)
    
    results.append(("Query Decision", test_query_decision()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Phase 3 Arbitration Engine is working!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Review logs above.")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
