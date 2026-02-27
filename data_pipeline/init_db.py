"""
Database Initialization Script
==============================
Create all tables required for Phase 1-4 of StormGuard
"""

from sqlalchemy import text
from api.utils.db import engine
from data_pipeline.db_models import Base, User, UserPreference, Alert, ChatMessage


def init_db():
    """Initialize database by creating all tables"""
    
    # Create all tables from SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    
    print("✓ Database tables initialized successfully")
    print("\nCreated tables:")
    print("  - users")
    print("  - user_preferences")
    print("  - alerts")
    print("  - chat_messages")


def drop_all_tables():
    """Drop all tables (USE WITH CAUTION)"""
    
    Base.metadata.drop_all(bind=engine)
    
    print("✓ All tables dropped")


def reset_db():
    """Drop all tables and recreate them"""
    
    drop_all_tables()
    init_db()
    
    print("✓ Database reset complete")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            init_db()
        elif command == "drop":
            import time
            print("WARNING: This will drop all tables!")
            print("Proceeding in 5 seconds... Press Ctrl+C to cancel")
            time.sleep(5)
            drop_all_tables()
        elif command == "reset":
            import time
            print("WARNING: This will reset the entire database!")
            print("Proceeding in 5 seconds... Press Ctrl+C to cancel")
            time.sleep(5)
            reset_db()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, drop, reset")
    else:
        init_db()
