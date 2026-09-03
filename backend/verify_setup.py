"""
Quick verification script to test Phase 1 setup
Run this to ensure all models and configuration work correctly
"""

import sys
from app.config import settings
from app.database import engine, Base
from app.models import (
    Merchant,
    Agent,
    Customer,
    Policy,
    AgentRequest,
    Decision,
    CustomerContact,
    AuditLog,
    DelayedAction,
)

def verify_config():
    """Verify configuration loads correctly"""
    print("✓ Checking configuration...")
    assert settings.DATABASE_URL, "DATABASE_URL not set"
    assert settings.REDIS_URL, "REDIS_URL not set"
    assert settings.DEFAULT_DAILY_CONTACT_LIMIT == 3
    assert settings.DEFAULT_PRIORITY_PAYMENT_RECOVERY == 100
    assert settings.DEFAULT_PRIORITY_WEIGHT == 0.6
    assert settings.DEFAULT_VALUE_WEIGHT == 0.4
    print("  ✓ Configuration loaded successfully")
    print(f"  ✓ Environment: {settings.ENVIRONMENT}")
    print(f"  ✓ Priority weight: {settings.DEFAULT_PRIORITY_WEIGHT}")
    print(f"  ✓ Value weight: {settings.DEFAULT_VALUE_WEIGHT}")

def verify_models():
    """Verify all models are importable"""
    print("\n✓ Checking models...")
    models = [
        Merchant,
        Agent,
        Customer,
        Policy,
        AgentRequest,
        Decision,
        CustomerContact,
        AuditLog,
        DelayedAction,
    ]
    for model in models:
        print(f"  ✓ {model.__name__} imported successfully")
    
    # Check that AgentRequest has new fields
    assert hasattr(AgentRequest, 'estimated_value'), "AgentRequest missing estimated_value field"
    assert hasattr(AgentRequest, 'urgency'), "AgentRequest missing urgency field"
    print("  ✓ AgentRequest has business value fields (estimated_value, urgency)")

def verify_database_connection():
    """Verify database connection"""
    print("\n✓ Checking database connection...")
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("  ✓ Database connection successful")
            return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        print("  ℹ Make sure PostgreSQL is running:")
        print("    docker-compose up -d postgres")
        return False

def main():
    """Run all verifications"""
    print("=" * 60)
    print("CONCORD Phase 1 Verification")
    print("=" * 60)
    
    try:
        verify_config()
        verify_models()
        db_ok = verify_database_connection()
        
        print("\n" + "=" * 60)
        if db_ok:
            print("✓ ALL CHECKS PASSED")
            print("\nNext steps:")
            print("1. Run migrations: alembic upgrade head")
            print("2. Start backend: uvicorn app.main:app --reload")
            print("3. Visit: http://localhost:8000/docs")
        else:
            print("⚠ Database connection failed, but models and config OK")
            print("\nStart database and retry:")
            print("  docker-compose up -d postgres")
            print("  python verify_setup.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
