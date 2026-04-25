"""Dashboard page for financial summary and overview.

Displays key financial metrics, year-to-date trends, and expense breakdowns
through interactive charts and KPI cards. Allows month selection for viewing
historical data.
"""

from __future__ import annotations

from datetime import datetime
from nicegui import ui

from ...domain.services import BudgetService
from ...domain.auth_service import AuthService


def _money(v: float) -> str:
    """Format float value as currency string.

    Args:
        v (float): Value to format.

    Returns:
        str: Formatted currency string (e.g., "$1,234.56").
    """
    return f"CHF {v:,.2f}"


def dashboard_page(service: BudgetService, auth_service: AuthService) -> None:
    """Render the financial dashboard page.

    Displays summary KPIs, year-to-date trends, and category breakdowns
    with interactive charts. Allows selection of different months to view.

    Args:
        service (BudgetService): Application service for data access.
        auth_service (AuthService): Authentication service for current user.
    """
    current_user = auth_service.current_user
    if not current_user:
        ui.label("Please log in to view the dashboard").classes("text-center mt-4")
        return
    user_id = current_user.id
    
    months = service.list_months_available(user_id)
    now = datetime.now()
    # Always default to current month, whether it has data or not
    default_year, default_month = (now.year, now.month)
    
    # Ensure current month is in the options
    current_month_tuple = (default_year, default_month)
    all_months = sorted(set(months + [current_month_tuple]), reverse=True) if months else [current_month_tuple]

    with ui.element('div').classes('page-wrap'):
        ui.label('Financial Summary & Overview').classes('section-title')

        # Month selector with responsive width
        with ui.row().classes('w-full justify-center mt-4 px-2'):
            month_select = ui.select(
                options=[f"{y}-{m:02d}" for y, m in all_months],
                value=f"{default_year}-{default_month:02d}",
                label='Select Month',
            ).props('outlined dense').classes('w-full md:w-1/2 lg:w-1/3')

        header_label = ui.label('').classes('text-2xl font-bold text-center mt-6 text-gray-800')

        # KPI cards grid - responsive layout
        with ui.row().classes('w-full justify-center gap-4 mt-6 px-2 flex-wrap'):
            # YTD Expenses
            with ui.element('div').classes('card kpi w-full sm:w-60 bg-gradient-to-br from-red-50 to-red-100 border-l-4 border-red-500'):
                ui.label('YTD Expenses').classes('kpi-label text-red-600 font-semibold')
                kpi_ytd_exp = ui.label('$0.00').classes('kpi-value text-red-700')

            # YTD Savings  
            with ui.element('div').classes('card kpi w-full sm:w-60 bg-gradient-to-br from-green-50 to-green-100 border-l-4 border-green-500'):
                ui.label('YTD Savings').classes('kpi-label text-green-600 font-semibold')
                kpi_ytd_sav = ui.label('$0.00').classes('kpi-value text-green-700')

            # Monthly Average
            with ui.element('div').classes('card kpi w-full sm:w-60 bg-gradient-to-br from-blue-50 to-blue-100 border-l-4 border-blue-500'):
                ui.label('Monthly average expenses YTD').classes('kpi-label text-blue-600 font-semibold')
                kpi_monthly_avg = ui.label('$0.00').classes('kpi-value text-blue-700')

            # Monthly Budget
            with ui.element('div').classes('card kpi w-full sm:w-60 bg-gradient-to-br from-purple-50 to-purple-100 border-l-4 border-purple-500'):
                ui.label('Budget Limit').classes('kpi-label text-purple-600 font-semibold')
                kpi_monthly_bud = ui.label('$0.00').classes('kpi-value text-purple-700')

        # Charts row (responsive)
        with ui.row().classes('w-full justify-center gap-6 mt-8 px-2 flex-wrap'):
            # Line chart for YTD trends
            with ui.element('div').classes('card w-full lg:w-1/2 p-4 min-w-0'):
                ui.label('YTD Savings Trend').classes('font-semibold text-center mb-3 text-gray-700')
                line_chart = ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Income", "Expenses", "Savings"], "textStyle": {"color": "#666"}},
                    "grid": {"left": "3%", "right": "3%", "bottom": "3%", "containLabel": True},
                    "xAxis": {"type": "category", "data": [], "axisLine": {"lineStyle": {"color": "#ddd"}}},
                    "yAxis": {"type": "value", "axisLine": {"lineStyle": {"color": "#ddd"}}},
                    "series": [
                        {"name": "Income", "type": "line", "data": [], "smooth": True, "itemStyle": {"color": "#10b981"}},
                        {"name": "Expenses", "type": "line", "data": [], "smooth": True, "itemStyle": {"color": "#ef4444"}},
                        {"name": "Savings", "type": "line", "data": [], "smooth": True, "itemStyle": {"color": "#3b82f6"}},
                    ],
                }).classes('h-80 w-full')

            # Donut chart for category breakdown
            with ui.element('div').classes('card w-full lg:w-1/2 p-4 min-w-0'):
                ui.label('Expenses by Category').classes('font-semibold text-center mb-3 text-gray-700')
                donut = ui.echart({
                    "tooltip": {"trigger": "item", "formatter": "{b}: ${c}"},
                    "legend": {"orient": "vertical", "left": "left", "textStyle": {"color": "#666"}},
                    "series": [{
                        "name": "Expenses",
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "avoidLabelOverlap": True,
                        "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
                        "label": {"show": False},
                        "emphasis": {"label": {"show": True, "fontSize": 12, "fontWeight": "bold"}},
                        "labelLine": {"show": False},
                        "data": [],
                    }],
                }).classes('h-80 w-full')

        def refresh() -> None:
            """Update all charts and KPIs based on selected month."""
            if not month_select.value:
                return

            y, m = month_select.value.split('-')
            year, month = int(y), int(m)

            # Update header with selected month name
            header_label.text = datetime(year, month, 1).strftime('%B %Y')

            # Update KPI cards
            s = service.get_summary(user_id, year, month)
            kpi_ytd_exp.text = _money(s["ytd_expenses"])
            kpi_ytd_sav.text = _money(s["ytd_savings"])
            kpi_monthly_avg.text = _money(s["monthly_average"])
            kpi_monthly_bud.text = _money(s["monthly_budget"])

            # Update line chart with YTD series
            series = service.ytd_series(user_id, year, month)
            x = [datetime(year, mm, 1).strftime('%b') for mm in series["months"]]
            line_chart.options["xAxis"]["data"] = x
            line_chart.options["series"][0]["data"] = series["income"]
            line_chart.options["series"][1]["data"] = series["expenses"]
            line_chart.options["series"][2]["data"] = series["savings"]
            line_chart.update()

            # Update donut chart with category breakdown
            cat = service.expenses_by_category(user_id, year, month)
            donut.options["series"][0]["data"] = [{"name": n, "value": v} for n, v in cat]
            donut.update()

        # Wire up month selector
        month_select.on('update:model-value', lambda _: refresh())
        refresh()