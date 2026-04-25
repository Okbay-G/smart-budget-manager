"""Application layout and styling for the budget management web app.

Defines the main shell layout including header navigation, styling,
and page routing. All pages are rendered within this consistent layout.
"""

from __future__ import annotations

from pathlib import Path

from nicegui import app as nicegui_app
from nicegui import ui

from ...services.budget_service import BudgetService
from ...services.auth_service import AuthService
from .pages_dashboard import dashboard_page
from .pages_budget import budget_page
from .pages_expenses import expenses_page
from .pages_income import income_page
from .pages_categories import categories_page
from .pages_auth import auth_page

# Serve the static folder so styles.css is available at /static/styles.css
_STATIC_DIR = Path(__file__).parent / "static"
nicegui_app.add_static_files("/static", str(_STATIC_DIR))


def _inject_css() -> None:
    """Inject global CSS stylesheet link for consistent design.

    Adds a <link> element pointing to the external stylesheet served from
    the /static directory. Keeping CSS in a dedicated file makes it easy
    to edit styles without touching Python source code.
    """
    ui.add_head_html('<link rel="stylesheet" href="/static/styles.css">')


def _layout_shell(content_builder, *, active_path: str, auth_service: AuthService) -> None:
    """Render the application shell with header and navigation.

    Args:
        content_builder: Callable that renders the page content.
        active_path (str): Current page path for active nav button highlighting.
        auth_service (AuthService): Authentication service for logout.
    """
    _inject_css()

    def nav_button(label: str, path: str) -> None:
        """Create a navigation button.

        Args:
            label (str): Button label text.
            path (str): Route path for button.
        """
        classes = "navbtn navbtn-active" if path == active_path else "navbtn"
        ui.button(label, on_click=lambda p=path: ui.navigate.to(p)).props("flat").classes(classes)

    with ui.header().classes("bg-gradient-to-r from-gray-900 to-gray-800 text-white"):
        with ui.element("div").classes("topbar"):
            with ui.element("div").classes("topbar-left"):
                ui.label("Budget Manager").classes("text-lg sm:text-xl font-bold tracking-tight")

            with ui.element("div").classes("topbar-mid"):
                with ui.row().classes("items-center no-wrap gap-2 sm:gap-3"):
                    nav_button("Overview", "/")
                    nav_button("Budget", "/budget")
                    nav_button("Expenses", "/expenses")
                    nav_button("Income", "/income")
                    nav_button("Categories", "/categories")

            with ui.element("div").classes("topbar-right"):
                def logout_handler() -> None:
                    """Handle logout action."""
                    auth_service.logout()
                    ui.navigate.to("/auth")
                
                user = auth_service.current_user
                if user:
                    # User profile display with icon
                    with ui.row().classes("items-center gap-2"):
                        ui.html("👤").classes("text-2xl")
                        ui.label(user.username).classes("text-lg font-semibold text-white")
                ui.button("Logout", on_click=logout_handler).props("unelevated").classes("authbtn")

    content_builder()


def build_layout(service: BudgetService, auth_service: AuthService) -> None:
    """Build application routes and page layout with authentication.

    Defines all application routes and wires them to their respective page renderers.
    Authentication required for accessing budget pages.

    Args:
        service (BudgetService): Application service for data access.
        auth_service (AuthService): Authentication service for user login/signup.
    """
    # Root page - redirect to auth if not logged in
    @ui.page("/")
    def _root() -> None:
        """Root page route - redirects to auth or dashboard."""
        if not auth_service.is_logged_in():
            auth_page(auth_service)
        else:
            _layout_shell(lambda: dashboard_page(service, auth_service), active_path="/", auth_service=auth_service)

    # Authentication page - no login required
    @ui.page("/auth")
    def _auth() -> None:
        """Authentication page route."""
        auth_page(auth_service)
    
    # Protected pages - require login
    @ui.page("/dashboard")
    def _dashboard() -> None:
        """Dashboard page route."""
        if not auth_service.is_logged_in():
            auth_page(auth_service)
            return
        _layout_shell(lambda: dashboard_page(service, auth_service), active_path="/", auth_service=auth_service)

    @ui.page("/budget")
    def _budget() -> None:
        """Budget management page route."""
        if not auth_service.is_logged_in():
            auth_page(auth_service)
            return
        _layout_shell(lambda: budget_page(service, auth_service), active_path="/budget", auth_service=auth_service)

    @ui.page("/expenses")
    def _expenses() -> None:
        """Expenses page route."""
        if not auth_service.is_logged_in():
            auth_page(auth_service)
            return
        _layout_shell(lambda: expenses_page(service, auth_service), active_path="/expenses", auth_service=auth_service)

    @ui.page("/income")
    def _income() -> None:
        """Income page route."""
        if not auth_service.is_logged_in():
            auth_page(auth_service)
            return
        _layout_shell(lambda: income_page(service, auth_service), active_path="/income", auth_service=auth_service)

    @ui.page("/categories")
    def _categories() -> None:
        """Categories management page route."""
        if not auth_service.is_logged_in():
            auth_page(auth_service)
            return
        _layout_shell(lambda: categories_page(service, auth_service), active_path="/categories", auth_service=auth_service)