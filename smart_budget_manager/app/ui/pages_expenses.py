"""Expenses management page for recording and viewing transactions.

Allows users to add, edit, and delete expense transactions. Provides filtering
by month and search capabilities.
"""

from __future__ import annotations

from datetime import date, datetime
from nicegui import ui

from ...domain.services import BudgetService
from ...domain.models import TxType
from ...domain.auth_service import AuthService


def _money(v: float) -> str:
    return f"CHF {v:,.2f}"


def expenses_page(service: BudgetService, auth_service: AuthService) -> None:
    current_user = auth_service.current_user
    if not current_user:
        ui.label("Please log in to view expenses").classes("text-center mt-4")
        return
    user_id = current_user.id
    
    def months_options() -> list[str]:
        return [f"{y}-{m:02d}" for y, m in service.list_months_available(user_id)]

    months = months_options()
    now = datetime.now()
    # Always default to current month, whether it has data or not
    default_value = f"{now.year}-{now.month:02d}"
    
    # Ensure current month is in the options
    all_month_options = sorted(set(months + [default_value]), reverse=True) if months else [default_value]

    accounts = service.list_accounts(user_id)
    categories = service.list_categories(user_id)

    acc_options = {a.id: a.name for a in accounts}
    cat_options = {c.id: c.name for c in categories}

    with ui.element("div").classes("page-wrap"):
        ui.label("Expenses").classes("section-title")
        ui.label("Add, edit, and remove expenses.").classes("muted mt-2")

        # Filters
        with ui.row().classes("w-full items-end gap-3 mt-4"):
            month_select = ui.select(
                options=all_month_options,
                value=default_value,
                label="Month",
            ).props("outlined dense").classes("w-full md:w-56")

            search = ui.input(label="Search description").props("outlined dense").classes("w-full md:w-96")

        # Add account inline if none exist yet
        with ui.element("div").classes("card p-4 mt-6"):
            ui.label("Accounts").classes("font-semibold")
            new_acc_input = ui.input(label="New account name", placeholder="e.g. Bank, Cash").props("outlined dense").classes("w-full md:w-64 mt-2")

            def create_account() -> None:
                name = (new_acc_input.value or "").strip()
                if not name:
                    ui.notify("Enter an account name", type="warning")
                    return
                acc = service.add_account(user_id, name)
                acc_options[acc.id] = acc.name
                account_in.options = acc_options
                account_in.value = acc.id
                account_in.update()
                edit_account.options = acc_options
                edit_account.update()
                new_acc_input.value = ""
                ui.notify(f'Account "{acc.name}" created')

            ui.button("Add Account", on_click=create_account).props("unelevated").classes("mt-2")

        # Add Expense
        with ui.element("div").classes("card p-4 mt-4"):
            ui.label("Add Expense").classes("font-semibold")

            with ui.row().classes("w-full gap-3 mt-3 items-end"):
                account_in = ui.select(
                    options=acc_options,
                    value=accounts[0].id if accounts else None,
                    label="Account",
                ).props("outlined dense").classes("w-full md:w-48")

                category_in = ui.select(
                    options=cat_options,
                    value=categories[0].id if categories else None,
                    label="Category",
                ).props("outlined dense").classes("w-full md:w-52")

                date_in = ui.input(label="Date", value=datetime.now().isoformat()).props("outlined dense type=date").classes("w-full md:w-44")

                amount_in = ui.number(label="Amount", value=100.0, format="%.2f", min=0).props(
                    "outlined dense"
                ).classes("w-full md:w-40")

                desc_in = ui.input(label="Description").props("outlined dense").classes("w-full md:flex-1")

                ui.button("Add", on_click=lambda: add_expense())

        # Table
        ui.label("Expenses for Selected Month").classes("font-semibold mt-8")

        table = ui.table(
            columns=[
                {"name": "date", "label": "Date", "field": "date", "sortable": True},
                {"name": "account", "label": "Account", "field": "account", "sortable": True},
                {"name": "category", "label": "Category", "field": "category", "sortable": True},
                {"name": "amount", "label": "Amount", "field": "amount", "sortable": True},
                {"name": "description", "label": "Description", "field": "description", "sortable": True},
                {"name": "actions", "label": "Actions", "field": "actions"},
            ],
            rows=[],
            row_key="id",
        ).classes("w-full mt-3").props("dense")

        total_label = ui.label("Total Expenses: CHF 0.00").classes("text-base font-semibold mt-4 text-right")

        # -------- Edit dialog --------
        edit_state: dict[str, object] = {"row": None}

        with ui.dialog() as edit_dialog, ui.card().classes("w-full max-w-2xl"):
            ui.label("Edit Expense").classes("text-lg font-semibold")
            ui.separator()

            with ui.row().classes("w-full gap-3 mt-3 items-end"):
                edit_account = ui.select(options=acc_options, label="Account").props("outlined dense").classes(
                    "w-full md:w-52"
                )
                edit_category = ui.select(options=cat_options, label="Category").props("outlined dense").classes(
                    "w-full md:w-60"
                )
                edit_date = ui.input(label="Date").props("outlined dense type=date").classes("w-full md:w-44")
                edit_amount = ui.number(label="Amount", format="%.2f", min=0).props("outlined dense").classes(
                    "w-full md:w-40"
                )
                edit_desc = ui.input(label="Description").props("outlined dense").classes("w-full md:flex-1")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=edit_dialog.close).props("flat")
                ui.button("Save", on_click=lambda: save_edit()).props("unelevated")

        # ---------- Helpers ----------

        def selected_year_month() -> tuple[int, int]:
            y, m = month_select.value.split("-")
            return int(y), int(m)

        def parse_iso_date(s: str) -> date | None:
            try:
                if isinstance(s, date):
                    return s
                return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
            except Exception:
                return None

        def refresh() -> None:
            year, month = selected_year_month()
            q = (search.value or "").strip().lower()

            id_to_acc = {a.id: a.name for a in service.list_accounts(user_id)}
            id_to_cat = {c.id: c.name for c in service.list_categories(user_id)}

            txs = service.list_transactions(user_id, year, month)
            rows = []
            total = 0.0

            for t in txs:
                if t.tx_type != TxType.EXPENSE:
                    continue
                if q and q not in t.description.lower():
                    continue

                total += float(t.amount)

                rows.append(
                    {
                        "id": t.id,
                        "date": t.tx_date.isoformat(),
                        "account": id_to_acc.get(t.account_id, "-"),
                        "category": id_to_cat.get(t.category_id, "-"),
                        "amount": _money(t.amount),
                        "description": t.description,
                        "_account_id": t.account_id,
                        "_category_id": t.category_id,
                        "_amount_raw": t.amount,
                        "_desc": t.description,
                        "_date_iso": t.tx_date.isoformat(),
                    }
                )

            table.rows = rows
            table.update()
            total_label.text = f"Total Expenses: {_money(total)}"

        def add_expense() -> None:
            if account_in.value is None or category_in.value is None:
                ui.notify("Select account and category", type="warning")
                return

            d = parse_iso_date(str(date_in.value or ""))
            if d is None:
                ui.notify("Please select a valid date", type="warning")
                return

            amt = float(amount_in.value or 0)
            if amt <= 0:
                ui.notify("Amount must be greater than 0", type="warning")
                return

            desc = str(desc_in.value or "").strip()
            if not desc:
                ui.notify("Please add a description", type="warning")
                return

            # Validate budget for this category
            category_id = int(category_in.value)
            can_add, reason = service.can_add_expense(user_id, category_id, amt, d.year, d.month)
            if not can_add:
                ui.notify(reason, type="negative")
                return

            service.add_expense(
                user_id,
                account_id=int(account_in.value),
                category_id=category_id,
                amount=float(amt),
                description=desc,
                tx_date=d,
            )

            ui.notify("Expense added")
            desc_in.value = ""
            refresh()

        def open_edit_dialog(row: dict) -> None:
            edit_state["row"] = row
            edit_account.value = int(row["_account_id"])
            edit_category.value = int(row["_category_id"])
            edit_date.value = str(row["_date_iso"])
            edit_amount.value = float(row["_amount_raw"])
            edit_desc.value = str(row["_desc"])
            edit_dialog.open()

        def save_edit() -> None:
            row = edit_state.get("row")
            if not isinstance(row, dict):
                return

            if edit_account.value is None or edit_category.value is None:
                ui.notify("Select account and category", type="warning")
                return

            d = parse_iso_date(str(edit_date.value or ""))
            if d is None:
                ui.notify("Please select a valid date", type="warning")
                return

            amt = float(edit_amount.value or 0)
            if amt <= 0:
                ui.notify("Amount must be greater than 0", type="warning")
                return

            desc = str(edit_desc.value or "").strip()
            if not desc:
                ui.notify("Please add a description", type="warning")
                return

            # Validate budget for this category (check amount difference)
            category_id = int(edit_category.value)
            old_amount = float(row["_amount_raw"])
            amount_difference = amt - old_amount
            
            if amount_difference > 0:  # Only validate if amount increased
                can_add, reason = service.can_add_expense(user_id, category_id, amount_difference, d.year, d.month)
                if not can_add:
                    ui.notify(reason, type="negative")
                    return

            service.update_expense(
                user_id,
                int(row["id"]),
                account_id=int(edit_account.value),
                category_id=category_id,
                amount=float(amt),
                description=desc,
                tx_date=d,
            )

            edit_dialog.close()
            ui.notify("Expense updated")
            refresh()

        def delete_expense(row: dict) -> None:
            service.delete_expense(user_id, int(row["id"]))
            ui.notify("Expense deleted")
            refresh()

        # Action buttons slot
        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense icon="edit" @click="$parent.$emit('edit_expense', props.row)" />
                <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('delete_expense', props.row)" />
              </div>
            </q-td>
            """,
        )
        table.on("edit_expense", lambda e: open_edit_dialog(e.args))
        table.on("delete_expense", lambda e: delete_expense(e.args))

        month_select.on("update:model-value", lambda _: refresh())
        search.on("update:model-value", lambda _: refresh())

        refresh()