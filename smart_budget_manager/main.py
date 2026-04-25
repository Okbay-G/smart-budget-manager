"""Smart Budget Manager - Main Application Entry Point.

"""

import logging
import signal
import sys
from pathlib import Path

# Ensure the project root is on sys.path when running the file directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from nicegui import ui
except ImportError:
    print("Error: NiceGUI not installed. Install with: pip install nicegui")
    sys.exit(1)

# Import application services (from complete backend)
from smart_budget_manager.domain.services import BudgetService
from smart_budget_manager.domain.auth_service import AuthService
from smart_budget_manager.persistence.db import Db

logging.basicConfig(level= logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize and run the Smart Budget Application."""
    try:
        logger.info("Initializing database...")
        db = Db("budget.db")
        db.initialize()
        db_conn = db.get_connection()

        logger.info("Initializing AuthService...")
        auth_service = AuthService(db_conn)

        logger.info("Initializing BudgetService...")
        service = BudgetService(db)

        logger.info("Building UI routes...")
        # Import and build layout (defined in app/ui/layout.py)
        from smart_budget_manager.app.ui.layout import build_layout
        build_layout(service, auth_service)

        def shutdown_handler(signum, frame):
            logger.info("Shutdown signal received")
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        logger.info("Starting NiceGUI server on port 8080...")
        print("Smart Budget Manager running on http://localhost:8080")
        ui.run(title='Smart Budget Manager', port=8080, reload=False)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ in {"__main__", "__mp_main__"}:
    main()
