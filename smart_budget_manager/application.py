"""Application bootstrap — service wiring and NiceGUI initialisation.

Separates bootstrap concerns (DB setup, service creation, route registration)
from the entry-point file so the package can be launched either via
``python main.py`` or ``python -m smart_budget_manager``.
"""

from __future__ import annotations

import logging
import sys

try:
    from nicegui import app as nicegui_app
    from nicegui import ui
except ImportError:
    print("Error: NiceGUI not installed. Install with: pip install nicegui")
    sys.exit(1)

from .services.budget_service import BudgetService
from .services.auth_service import AuthService
from .data_access.db import Db
from .app.ui.layout import build_layout

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def bootstrap(db_path: str = "budget.db") -> None:
    """Wire services, register UI routes, and start the application.

    Args:
        db_path: Path to the SQLite database file.
    """
    try:
        logger.info("Initializing database...")
        db = Db(db_path)
        db.initialize()

        logger.info("Initializing services...")
        auth_service = AuthService(db)
        service = BudgetService(db)

        logger.info("Building UI routes...")
        build_layout(service, auth_service)

        def on_shutdown() -> None:
            logger.info("Shutdown signal received")

        nicegui_app.on_shutdown(on_shutdown)

        logger.info("Starting NiceGUI server on port 8080...")
        print("Smart Budget Manager running on http://localhost:8080")
        ui.run(title="Smart Budget Manager", port=8080, reload=False)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Application error: {e}")
        sys.exit(1)
