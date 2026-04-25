"""Application layout and styling for the budget management web app.

Defines the main shell layout including header navigation, styling,
and page routing. All pages are rendered within this consistent layout.
"""

from __future__ import annotations

from nicegui import ui

from ...domain.services import BudgetService
from ...domain.auth_service import AuthService
from .pages_dashboard import dashboard_page
from .pages_budget import budget_page
from .pages_expenses import expenses_page
from .pages_income import income_page
from .pages_categories import categories_page
from .pages_auth import auth_page


def _inject_css() -> None:
    """Inject global CSS styling for consistent design.

    Adds variable definitions, component styles, and responsive layout rules
    to ensure a cohesive, modern look across all pages.
    """
    ui.add_head_html(
        """
        <style>
          :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --danger: #ef4444;
            --success: #10b981;
            --warning: #f59e0b;
            --info: #3b82f6;
          }

          body { 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
          }

          .page-wrap { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
          }

          .section-title { 
            font-size: 24px; 
            font-weight: 700; 
            color: #1f2937; 
            margin-bottom: 16px;
            letter-spacing: -0.5px;
          }

          .muted { 
            color: #6b7280; 
            font-size: 13px;
          }

          .card { 
            background: white; 
            border-radius: 16px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
          }

          .card:hover {
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
            transform: translateY(-2px);
          }

          .kpi { 
            padding: 18px 20px; 
            position: relative;
            overflow: hidden;
          }

          .kpi::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 80px;
            height: 80px;
            background: rgba(255,255,255,0.5);
            border-radius: 50%;
            transform: translate(20px, -20px);
          }

          .kpi-label { 
            font-size: 12px; 
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
          }

          .kpi-value { 
            font-size: 32px; 
            font-weight: 800; 
            color: #111827; 
            line-height: 1;
            margin-top: 8px;
            position: relative;
            z-index: 1;
          }

          .topbar {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 8px 0;
          }

          .topbar-left  { 
            flex: 0 0 auto; 
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .topbar-mid   { 
            flex: 1 1 auto; 
            min-width: 320px; 
            display: flex; 
            justify-content: center; 
          }

          .topbar-right { 
            flex: 0 0 auto; 
            display: flex; 
            gap: 10px;
            flex-wrap: wrap;
          }

          .navbtn {
            border-radius: 10px !important;
            padding: 8px 16px !important;
            min-height: 40px !important;
            white-space: nowrap !important;
            font-size: 16px !important;
            transition: all 0.2s ease !important;
          }

          .navbtn .q-btn__content {
            color: rgba(255,255,255,0.85) !important;
            font-weight: 600 !important;
            text-transform: none !important;
            letter-spacing: 0.2px;
          }

          .navbtn:hover { 
            background: rgba(255,255,255,0.15) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
          }

          .navbtn-active {
            background: rgba(255,255,255,0.25) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
          }

          .navbtn-active .q-btn__content {
            color: #ffffff !important;
            font-weight: 700 !important;
          }

          .authbtn {
            background: rgba(255,255,255,0.12) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: 10px !important;
            padding: 6px 14px !important;
            min-height: 36px !important;
            white-space: nowrap !important;
            font-size: 13px !important;
          }

          .authbtn .q-btn__content {
            color: #ffffff !important;
            font-weight: 700 !important;
            text-transform: none !important;
          }

          .authbtn:hover { 
            background: rgba(255,255,255,0.18) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
          }

          .authbtn-primary {
            background: var(--primary) !important;
            border: 1px solid var(--primary) !important;
          }

          .authbtn-primary:hover { 
            background: var(--primary-dark) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
          }

          header.q-header { 
            overflow: visible !important;
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%) !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
          }

          /* Responsive adjustments */
          @media (max-width: 768px) {
            .page-wrap { padding: 12px; }
            .section-title { font-size: 20px; }
            .topbar { flex-direction: column; align-items: stretch; gap: 8px; }
            .topbar-mid { justify-content: flex-start; }
            .navbtn { padding: 4px 10px !important; font-size: 11px !important; }
          }
        </style>
        """
    )


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