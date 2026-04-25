"""Monthly budget management page for setting spending limits.

Allows users to set and manage spending limits (budgets) for different expense
categories on a monthly basis.
"""

from __future__ import annotations

from datetime import datetime
from nicegui import ui

from ...services.budget_service import BudgetService
from ...services.auth_service import AuthService
from .controllers import BudgetController
from .utils import money as _money


def budget_page(service: BudgetService, auth_service: AuthService) -> None:
    current_user = auth_service.current_user
    if not current_user:
        ui.label("Please log in to manage budgets").classes("text-center mt-4")
        return
    user_id = current_user.id
    budget_ctrl = BudgetController(service)

    now = datetime.now()
    months = service.list_months_available(user_id)
    # Always default to current month, whether it has data or not
    default_year, default_month = (now.year, now.month)

    # Build future months: current month + next 11 months
    def _add_months(y: int, m: int, n: int) -> tuple[int, int]:
        m += n
        y += (m - 1) // 12
        m = (m - 1) % 12 + 1
        return y, m

    future_months = [_add_months(default_year, default_month, i) for i in range(12)]

    # Merge past months with data + future months, sort descending
    all_months = sorted(set(months) | set(future_months), reverse=True)

    categories = service.list_categories(user_id)
    cat_options = {c.id: c.name for c in categories}

    with ui.element("div").classes("page-wrap"):
        ui.label("Budget").classes("section-title")
        ui.label("Manage monthly budget limits per category.").classes("muted mt-2")

        # Month selector row
        with ui.row().classes("w-full items-end gap-3 mt-4"):
            month_select = ui.select(
                options=[f"{y}-{m:02d}" for y, m in all_months],
                value=f"{default_year}-{default_month:02d}",
                label="Month",
            ).props("outlined dense").classes("w-full md:w-60")

        # Add/Update budget card
        with ui.element("div").classes("card p-4 mt-6"):
            ui.label("Add / Update Budget").classes("font-semibold")

            with ui.row().classes("w-full gap-3 mt-3 items-end"):
                cat_select = ui.select(
                    options=cat_options,
                    value=categories[0].id if categories else None,
                    label="Category",
                ).props("outlined dense").classes("w-full md:w-72")

                limit_input = ui.number(
                    label="Monthly Limit",
                    value=200.0,
                    format="%.2f",
                    min=0,
                ).props("outlined dense").classes("w-full md:w-56")

                ui.button("Save Budget", on_click=lambda: save_budget()).classes("")

            ui.label(
                "Rule: if a budget for the selected category already exists for that month, it is overwritten."
            ).classes("muted mt-2 text-sm")

        ui.label("Budgets for Selected Month").classes("font-semibold mt-8")

        table = ui.table(
            columns=[
                {"name": "category", "label": "Category", "field": "category", "sortable": True},
                {"name": "limit", "label": "Limit", "field": "limit", "sortable": True},
                {"name": "spent", "label": "Spent", "field": "spent", "sortable": True},
                {"name": "remaining", "label": "Remaining", "field": "remaining", "sortable": True},
                {"name": "actions", "label": "Actions", "field": "actions"},
            ],
            rows=[],
            row_key="id",
        ).classes("w-full mt-3").props("dense")
        budget_empty_label = ui.label(
            "No budgets set for this month. Use the form above to add one."
        ).classes("text-center mt-4 text-gray-400 italic")
        budget_empty_label.set_visibility(False)

        # Budget utilization donut chart
        ui.label("Budget Utilization").classes("font-semibold mt-8")
        with ui.element("div").classes("card p-4 mt-3"):
            budget_chart = ui.echart({
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{b}: {c}",
                },
                "legend": {
                    "orient": "vertical",
                    "left": "left",
                    "textStyle": {"color": "#666"},
                },
                "series": [{
                    "name": "Spent",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "avoidLabelOverlap": True,
                    "itemStyle": {
                        "borderRadius": 8,
                        "borderColor": "#fff",
                        "borderWidth": 2,
                    },
                    "label": {"show": False},
                    "emphasis": {
                        "label": {"show": True, "fontSize": 12, "fontWeight": "bold"},
                    },
                    "labelLine": {"show": False},
                    "data": [],
                }],
            }).classes("h-80 w-full")
        budget_chart_empty = ui.label(
            "No budgets to display for this month."
        ).classes("text-center mt-2 text-gray-400 italic")
        budget_chart_empty.set_visibility(False)

        # ---------- Edit dialog (reliable) ----------
        edit_state = {"row": None}

        with ui.dialog() as edit_dialog, ui.card().classes("w-full max-w-md"):
            ui.label("Edit Budget").classes("text-lg font-semibold")
            ui.separator()
            edit_category_label = ui.label("").classes("muted mt-2")
            edit_limit_input = ui.number(label="Monthly Limit", format="%.2f", min=0).props("outlined dense").classes(
                "w-full mt-3"
            )

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=edit_dialog.close).props("flat")
                ui.button("Save", on_click=lambda: save_edit()).props("unelevated")

        # ---------- helpers ----------
        def selected_year_month() -> tuple[int, int]:
            y, m = month_select.value.split("-")
            return int(y), int(m)

        def refresh() -> None:
            year, month = selected_year_month()
            budgets = service.list_budgets(user_id, year, month)

            id_to_name = {c.id: c.name for c in service.list_categories(user_id)}
            rows = []
            for b in budgets:
                spent = service.get_category_spending(user_id, b.category_id, year, month)
                remaining = b.limit_amount - spent
                rows.append(
                    {
                        "id": b.id,
                        "category": id_to_name.get(b.category_id, f"Category {b.category_id}"),
                        "limit": _money(b.limit_amount),
                        "spent": _money(spent),
                        "remaining": _money(remaining),
                        "_category_id": b.category_id,
                        "_limit_amount": b.limit_amount,
                        "_year": b.year,
                        "_month": b.month,
                    }
                )
            table.rows = rows
            table.update()
            budget_empty_label.set_visibility(len(rows) == 0)

            # Update budget utilization donut chart
            chart_data = []
            for b in budgets:
                spent = service.get_category_spending(user_id, b.category_id, year, month)
                pct = (spent / b.limit_amount * 100) if b.limit_amount > 0 else 0
                cat_name = id_to_name.get(b.category_id, f"Category {b.category_id}")
                label = f"{cat_name} ({_money(spent)} / {_money(b.limit_amount)}, {pct:.0f}%)"
                chart_data.append({"name": label, "value": round(spent, 2)})

            has_spending = any(d["value"] > 0 for d in chart_data)
            budget_chart.set_visibility(has_spending)
            budget_chart_empty.set_visibility(not has_spending)
            if has_spending:
                budget_chart.options["series"][0]["data"] = chart_data
                budget_chart.update()

        def save_budget() -> None:
            if cat_select.value is None:
                ui.notify("Please select a category", type="warning")
                return

            year, month = selected_year_month()
            limit = float(limit_input.value or 0)

            if limit <= 0:
                ui.notify("Limit must be greater than 0", type="warning")
                return

            ok, msg = budget_ctrl.save(user_id, int(cat_select.value), year, month, limit)
            ui.notify(msg)
            refresh()

        def open_edit_dialog(row: dict) -> None:
            edit_state["row"] = row
            edit_category_label.text = f'Category: {row["category"]}'
            edit_limit_input.value = float(row["_limit_amount"])
            edit_dialog.open()

        def save_edit() -> None:
            row = edit_state.get("row")
            if not row:
                return

            new_limit = float(edit_limit_input.value or 0)
            if new_limit <= 0:
                ui.notify("Limit must be greater than 0", type="warning")
                return

            ok, msg = budget_ctrl.update(user_id, int(row["id"]), float(new_limit))
            edit_dialog.close()
            ui.notify(msg)
            refresh()

        def delete_budget(row: dict) -> None:
            ok, msg = budget_ctrl.delete(user_id, int(row["id"]))
            ui.notify(msg)
            refresh()

        # Action buttons slot
        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense icon="edit" @click="$parent.$emit('edit_budget', props.row)" />
                <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('delete_budget', props.row)" />
              </div>
            </q-td>
            """,
        )

        # Table events (sync handlers)
        table.on("edit_budget", lambda e: open_edit_dialog(e.args))
        table.on("delete_budget", lambda e: delete_budget(e.args))

        month_select.on("update:model-value", lambda _: refresh())
        refresh()