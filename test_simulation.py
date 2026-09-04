#!/usr/bin/env python3
"""
Quick test script to verify simulation endpoint works
"""
import requests
import json
import time

API_URL = "http://localhost:8000/api/v1"

def test_simulation():
    """Test simulation with minimal parameters"""
    print("🚀 Testing CONCORD Simulation API...")
    print("-" * 50)
    
    # Test simulation with small scale
    simulation_data = {
        "scenario_type": "high_volume",  # Valid scenario type
        "customer_count": 5,
        "duration_seconds": 60,  # Minimum required
        "speed_multiplier": 1.0,
        "create_customers": True
    }
    
    print("\n📋 Simulation Configuration:")
    print(f"  - Scenario: {simulation_data['scenario_type']}")
    print(f"  - Customers: {simulation_data['customer_count']}")
    print(f"  - Duration: {simulation_data['duration_seconds']}s")
    print(f"  - Speed: {simulation_data['speed_multiplier']}x")
    
    print("\n⏳ Starting simulation (this will take ~60 seconds)...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/simulation/run",
            json=simulation_data,
            timeout=90  # 90 second timeout
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Simulation completed in {elapsed:.1f} seconds!")
            print("\n📊 Results:")
            print(f"  - Simulation ID: {result['simulation_id']}")
            print(f"  - Total Requests: {result['total_requests']}")
            print(f"  - Customer Count: {result['customer_count']}")
            print(f"  - Duration: {result['duration_seconds']}s")
            
            if 'results' in result:
                print("\n  Decision Breakdown:")
                print(f"    • Allow: {result['results'].get('allow', 0)}")
                print(f"    • Block: {result['results'].get('block', 0)}")
                print(f"    • Delay: {result['results'].get('delay', 0)}")
                print(f"    • Merge: {result['results'].get('merge', 0)}")
                print(f"    • Errors: {result['results'].get('errors', 0)}")
            
            if 'metrics' in result:
                print("\n  Performance Metrics:")
                print(f"    • Requests/sec: {result['metrics'].get('requests_per_second', 0):.2f}")
                print(f"    • Allow rate: {result['metrics'].get('allow_rate', 0):.1f}%")
                print(f"    • Block rate: {result['metrics'].get('block_rate', 0):.1f}%")
            
            return True
        else:
            print(f"\n❌ Simulation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⚠️  Request timed out after {time.time() - start_time:.1f} seconds")
        print("Note: Simulation may still be running on the backend")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    print("\n" + "=" * 50)
    print("📈 Testing Metrics API...")
    print("-" * 50)
    
    try:
        response = requests.get(
            f"{API_URL}/executions/metrics/delivery?days=7",
            timeout=10
        )
        
        if response.status_code == 200:
            metrics = response.json()
            print("\n✅ Metrics endpoint working!")
            print(f"\n📊 Current Metrics:")
            print(f"  - Total Executions: {metrics.get('total_executions', 0)}")
            print(f"  - Delivered: {metrics.get('delivered', 0)}")
            print(f"  - Failed: {metrics.get('failed', 0)}")
            print(f"  - Delivery Rate: {metrics.get('delivery_rate', 0):.1f}%")
            return True
        else:
            print(f"\n❌ Metrics failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  CONCORD API Test Suite")
    print("=" * 50)
    
    # Test simulation
    sim_success = test_simulation()
    
    # Test metrics
    metrics_success = test_metrics()
    
    print("\n" + "=" * 50)
    print("  Test Summary")
    print("=" * 50)
    print(f"✅ Simulation: {'PASSED' if sim_success else 'FAILED'}")
    print(f"✅ Metrics: {'PASSED' if metrics_success else 'FAILED'}")
    print("=" * 50 + "\n")
