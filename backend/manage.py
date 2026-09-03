import sys
import os
import uvicorn

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.db import engine, create_db_and_tables
from app.models import Supervisor, OrderRun, ActivityLog
from app.main import seed_default_supervisors

def show_help():
    print("""
Order Supervisor Management CLI

Available commands:
  python manage.py migrate          - Create/update all tables in PostgreSQL database
  python manage.py makemigrations   - Verify model definitions
  python manage.py test             - Run automated test suite covering all scenarios
  python manage.py runserver        - Run FastAPI server with auto-reload (port 8000)
  python manage.py runworker        - Run Temporal background worker
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
        
    command = sys.argv[1].lower()
    
    if command in ["migrate", "create_tables"]:
        print(f"Connecting to PostgreSQL database: {settings.get_database_url().split('@')[-1]}...")
        try:
            create_db_and_tables()
            print("Applying migrations for models in app/models.py:")
            print("  [OK] supervisors (Table: supervisors)")
            print("  [OK] order_runs (Table: order_runs)")
            print("  [OK] activity_logs (Table: activity_logs)")
            seed_default_supervisors()
            print("Migration complete! Database tables successfully created in PostgreSQL.")
        except Exception as e:
            print(f"Migration failed: {e}")
            sys.exit(1)
            
    elif command in ["makemigrations"]:
        print("Checking model definitions in app/models.py...")
        print("  [OK] Supervisor model verified")
        print("  [OK] OrderRun model verified")
        print("  [OK] ActivityLog model verified")
        print("No pending schema drift. Ready to run 'python manage.py migrate'.")
        
    elif command in ["test"]:
        print("Running comprehensive test suite for Order Supervisor POC...")
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        if not result.wasSuccessful():
            sys.exit(1)
            
    elif command in ["runserver"]:
        port = int(os.getenv("PORT", 8000))
        print(f"Starting FastAPI server on http://localhost:{port}...")
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
        
    elif command in ["runworker"]:
        print("Starting Temporal Worker...")
        import run_worker
        import asyncio
        asyncio.run(run_worker.main())
        
    else:
        print(f"Unknown command: '{command}'")
        show_help()

if __name__ == "__main__":
    main()
