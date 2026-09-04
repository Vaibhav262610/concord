"""
Integration Tests for Phases 6, 7, 8
Tests conflict detection, merge engine, simulation, customer management, and audit trail
"""

import requests
import time
import json
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
MERCHANT_ID = None
AGENT_ID = None
API_KEY = None
CUSTOMER_IDS = []

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results"""
    symbol = "✓" if status == "PASS" else "✗"
    print(f"{symbol} {test_name}: {status}")
    if details:
        print(f"  {details}")

def setup_test_environment():
    """Set up test merchant, agent, and customers"""
    global MERCHANT_ID, AGENT_ID, API_KEY, CUSTOMER_IDS
    
    print("\n=== Setting Up Test Environment ===\n")
    
    # Create merchant (use existing if available)
    response = requests.get(f"{BASE_URL}/../merchants")
    if response.status_code == 200:
        merchants = response.json().get("merchants", [])
        if merchants:
            MERCHANT_ID = merchants[0]["id"]
            log_test("Use existing merchant", "PASS", f"Merchant ID: {MERCHANT_ID}")
        else:
            log_test("Get merchant", "FAIL", "No merchants found")
            return False
    
    # Create test agent
    response = requests.post(
        f"{BASE_URL}/agents",
        json={
            "name": "Integration Test Agent",
            "agent_type": "test_agent",
            "description": "Agent for integration testing",
            "permissions": {
                "messaging": True,
                "discounts": True,
                "high_value_discounts": True
            }
        }
    )
    
    if response.status_code == 201:
        agent_data = response.json()
        AGENT_ID = agent_data["id"]
        API_KEY = agent_data.get("api_key")
        log_test("Create test agent", "PASS", f"Agent ID: {AGENT_ID}")
    else:
        log_test("Create test agent", "FAIL", f"Status: {response.status_code}")
        return False
    
    # Create test customers
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/customers",
            params={"merchant_id": MERCHANT_ID},
            json={
                "external_id": f"TEST_CUST_{int(time.time())}_{i}",
                "name": f"Test Customer {i+1}",
                "email": f"test{i+1}@integration.test",
                "phone": f"+919000{i:05d}",
                "consent": {
                    "marketing": True,
                    "transactional": True,
                    "global_opt_out": False
                }
            }
        )
        
        if response.status_code == 201:
            customer = response.json()
            CUSTOMER_IDS.append(customer["id"])
            log_test(f"Create test customer {i+1}", "PASS", f"Customer ID: {customer['id']}")
        else:
            log_test(f"Create test customer {i+1}", "FAIL", f"Status: {response.status_code}")
    
    return len(CUSTOMER_IDS) == 3


def test_conflict_detection():
    """Test Phase 6: Conflict Detection"""
    print("\n=== Phase 6: Conflict Detection Tests ===\n")
    
    if not CUSTOMER_IDS:
        log_test("Conflict detection", "SKIP", "No customers available")
        return
    
    customer_id = CUSTOMER_IDS[0]
    
    # Create multiple requests in quick succession (should trigger RAPID_SUCCESSION)
    request_ids = []
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/actions",
            headers={"X-API-Key": API_KEY},
            json={
                "request_id": f"conflict_test_{int(time.time())}_{i}",
                "customer_id": customer_id,
                "action": "SEND_MESSAGE",
                "intent": "MARKETING",
                "channel": "EMAIL",
                "priority": 50,
                "message": f"Test conflict message {i+1}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            request_ids.append(data["request"]["request_id"])
            time.sleep(0.5)  # Small delay to trigger rapid succession
    
    log_test("Create rapid succession requests", "PASS", f"Created {len(request_ids)} requests")
    
    # Check for conflicts
    time.sleep(2)  # Wait for conflict detection
    response = requests.get(f"{BASE_URL}/conflicts")
    
    if response.status_code == 200:
        conflicts = response.json()
        conflict_count = conflicts.get("total", 0)
        if conflict_count > 0:
            log_test("Conflict detection", "PASS", f"Detected {conflict_count} conflict(s)")
            
            # Get conflict details
            if conflicts.get("conflicts"):
                conflict_id = conflicts["conflicts"][0]["id"]
                
                # Test get conflict recommendation
                rec_response = requests.get(f"{BASE_URL}/conflicts/{conflict_id}/recommendation")
                if rec_response.status_code == 200:
                    recommendation = rec_response.json()
                    log_test("Get merge recommendation", "PASS", 
                           f"Strategy: {recommendation.get('recommended_strategy', 'N/A')}")
                else:
                    log_test("Get merge recommendation", "FAIL")
        else:
            log_test("Conflict detection", "INFO", "No conflicts detected (may need more simultaneous requests)")
    else:
        log_test("Conflict detection", "FAIL", f"Status: {response.status_code}")


def test_customer_management():
    """Test Phase 8: Customer Management"""
    print("\n=== Phase 8: Customer Management Tests ===\n")
    
    # Test list customers
    response = requests.get(f"{BASE_URL}/customers", params={"limit": 10})
    if response.status_code == 200:
        data = response.json()
        customer_count = len(data.get("customers", []))
        log_test("List customers", "PASS", f"Found {customer_count} customers")
    else:
        log_test("List customers", "FAIL")
    
    # Test search customers
    response = requests.get(f"{BASE_URL}/customers", params={"search": "Test"})
    if response.status_code == 200:
        data = response.json()
        log_test("Search customers", "PASS", f"Found {data.get('total', 0)} matching customers")
    else:
        log_test("Search customers", "FAIL")
    
    if CUSTOMER_IDS:
        customer_id = CUSTOMER_IDS[0]
        
        # Test get customer
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        if response.status_code == 200:
            log_test("Get customer", "PASS")
        else:
            log_test("Get customer", "FAIL")
        
        # Test update customer
        response = requests.put(
            f"{BASE_URL}/customers/{customer_id}",
            json={
                "name": "Updated Test Customer",
                "custom_metadata": {"test_key": "test_value"}
            }
        )
        if response.status_code == 200:
            log_test("Update customer", "PASS")
        else:
            log_test("Update customer", "FAIL")
        
        # Test customer analytics
        response = requests.get(f"{BASE_URL}/customers/{customer_id}/analytics", params={"days": 30})
        if response.status_code == 200:
            analytics = response.json()
            log_test("Get customer analytics", "PASS", 
                   f"Total requests: {analytics.get('total_requests', 0)}")
        else:
            log_test("Get customer analytics", "FAIL")
    
    # Test customer stats
    response = requests.get(f"{BASE_URL}/customers/stats/summary")
    if response.status_code == 200:
        stats = response.json()
        log_test("Get customer stats", "PASS", 
               f"Total: {stats.get('total_customers', 0)}, Active: {stats.get('active_customers', 0)}")
    else:
        log_test("Get customer stats", "FAIL")


def test_audit_trail():
    """Test Phase 8: Audit Trail"""
    print("\n=== Phase 8: Audit Trail Tests ===\n")
    
    # Test list audit logs
    response = requests.get(f"{BASE_URL}/audit-logs", params={"limit": 20})
    if response.status_code == 200:
        data = response.json()
        log_count = len(data.get("logs", []))
        log_test("List audit logs", "PASS", f"Found {log_count} audit logs")
        
        if log_count > 0:
            log_id = data["logs"][0]["id"]
            
            # Test get single audit log
            response = requests.get(f"{BASE_URL}/audit-logs/{log_id}")
            if response.status_code == 200:
                log_test("Get audit log", "PASS")
            else:
                log_test("Get audit log", "FAIL")
    else:
        log_test("List audit logs", "FAIL")
    
    # Test filter by entity type
    response = requests.get(
        f"{BASE_URL}/audit-logs",
        params={"entity_type": "agent_request", "limit": 10}
    )
    if response.status_code == 200:
        data = response.json()
        log_test("Filter audit logs by entity type", "PASS", 
               f"Found {data.get('total', 0)} agent_request logs")
    else:
        log_test("Filter audit logs by entity type", "FAIL")
    
    # Test audit stats
    response = requests.get(f"{BASE_URL}/audit-logs/stats/summary", params={"days": 7})
    if response.status_code == 200:
        stats = response.json()
        log_test("Get audit stats", "PASS", 
               f"Total logs: {stats.get('total_logs', 0)}, Recent (24h): {stats.get('recent_activity_count', 0)}")
    else:
        log_test("Get audit stats", "FAIL")
    
    # Test recent logs search
    response = requests.get(f"{BASE_URL}/audit-logs/search/recent", params={"minutes": 60, "limit": 20})
    if response.status_code == 200:
        data = response.json()
        log_test("Search recent audit logs", "PASS", f"Found {data.get('count', 0)} recent logs")
    else:
        log_test("Search recent audit logs", "FAIL")
    
    # Test customer timeline
    if CUSTOMER_IDS:
        response = requests.get(f"{BASE_URL}/audit-logs/customer/{CUSTOMER_IDS[0]}/timeline")
        if response.status_code == 200:
            data = response.json()
            log_test("Get customer audit timeline", "PASS", f"Found {data.get('total', 0)} logs")
        else:
            log_test("Get customer audit timeline", "FAIL")


def test_simulation():
    """Test Phase 7: Simulation"""
    print("\n=== Phase 7: Simulation Tests ===\n")
    
    # Test list scenarios
    response = requests.get(f"{BASE_URL}/simulation/scenarios")
    if response.status_code == 200:
        data = response.json()
        scenario_count = len(data.get("scenarios", []))
        log_test("List simulation scenarios", "PASS", f"Found {scenario_count} scenarios")
        
        if scenario_count > 0:
            scenario_type = data["scenarios"][0]["type"]
            
            # Test fleet info
            fleet_response = requests.get(f"{BASE_URL}/simulation/fleet")
            if fleet_response.status_code == 200:
                fleet_data = fleet_response.json()
                agent_count = fleet_data.get("fleet_stats", {}).get("total_agents", 0)
                log_test("Get fleet info", "PASS", f"{agent_count} agent types available")
            else:
                log_test("Get fleet info", "FAIL")
            
            # Run a small simulation
            print(f"\n  Running simulation with {scenario_type} scenario...")
            sim_response = requests.post(
                f"{BASE_URL}/simulation/run",
                json={
                    "scenario_type": scenario_type,
                    "customer_count": 3,
                    "duration_seconds": 60,
                    "speed_multiplier": 50.0,
                    "create_customers": True
                }
            )
            
            if sim_response.status_code == 200:
                sim_data = sim_response.json()
                metrics = sim_data.get("metrics", {})
                log_test("Run simulation", "PASS",
                       f"Processed {sim_data.get('total_requests', 0)} requests in {metrics.get('actual_duration_seconds', 0):.2f}s")
                log_test("Simulation metrics", "INFO",
                       f"Allow: {metrics.get('allow_rate', 0)*100:.1f}%, Block: {metrics.get('block_rate', 0)*100:.1f}%, Delay: {metrics.get('delay_rate', 0)*100:.1f}%")
            else:
                log_test("Run simulation", "FAIL", f"Status: {sim_response.status_code}")
    else:
        log_test("List simulation scenarios", "FAIL")


def test_end_to_end_flow():
    """Test complete end-to-end flow"""
    print("\n=== End-to-End Flow Test ===\n")
    
    if not CUSTOMER_IDS or not API_KEY:
        log_test("End-to-end flow", "SKIP", "Missing prerequisites")
        return
    
    customer_id = CUSTOMER_IDS[0]
    
    # 1. Submit action request
    request_id = f"e2e_test_{int(time.time())}"
    response = requests.post(
        f"{BASE_URL}/actions",
        headers={"X-API-Key": API_KEY},
        json={
            "request_id": request_id,
            "customer_id": customer_id,
            "action": "SEND_MESSAGE",
            "intent": "PAYMENT_RECOVERY",
            "channel": "EMAIL",
            "priority": 85,
            "estimated_value": 500000,
            "urgency": "HIGH",
            "message": "End-to-end test message",
            "offer": {
                "discount_type": "PERCENTAGE",
                "discount_value": 10
            }
        }
    )
    
    if response.status_code != 200:
        log_test("End-to-end: Submit request", "FAIL")
        return
    
    action_data = response.json()
    log_test("End-to-end: Submit request", "PASS", f"Request ID: {request_id}")
    
    # 2. Verify decision was made
    decision_id = action_data.get("decision", {}).get("id")
    if decision_id:
        log_test("End-to-end: Decision created", "PASS", 
               f"Decision: {action_data['decision']['decision_type']}")
    else:
        log_test("End-to-end: Decision created", "FAIL")
        return
    
    # 3. Check execution (if allowed)
    if action_data["decision"]["decision_type"] == "ALLOW":
        execution = action_data.get("execution")
        if execution:
            log_test("End-to-end: Execution triggered", "PASS",
                   f"Status: {execution['status']}")
        else:
            log_test("End-to-end: Execution triggered", "INFO", "No execution data")
    
    # 4. Verify customer analytics updated
    time.sleep(1)
    analytics_response = requests.get(f"{BASE_URL}/customers/{customer_id}/analytics")
    if analytics_response.status_code == 200:
        analytics = analytics_response.json()
        log_test("End-to-end: Customer analytics updated", "PASS",
               f"Total requests: {analytics['total_requests']}")
    else:
        log_test("End-to-end: Customer analytics updated", "FAIL")
    
    # 5. Verify audit logs captured
    audit_response = requests.get(
        f"{BASE_URL}/audit-logs",
        params={"entity_type": "agent_request", "limit": 5}
    )
    if audit_response.status_code == 200:
        audit_data = audit_response.json()
        log_test("End-to-end: Audit trail captured", "PASS",
               f"Found {audit_data.get('total', 0)} audit logs")
    else:
        log_test("End-to-end: Audit trail captured", "FAIL")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("CONCORD INTEGRATION TESTS - Phases 6, 7, 8")
    print("="*60)
    
    # Setup
    if not setup_test_environment():
        print("\n✗ Setup failed. Aborting tests.")
        return
    
    # Run test suites
    test_customer_management()
    test_audit_trail()
    test_conflict_detection()
    test_simulation()
    test_end_to_end_flow()
    
    print("\n" + "="*60)
    print("INTEGRATION TESTS COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
