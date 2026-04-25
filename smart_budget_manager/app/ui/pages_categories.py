"""Categories management page for creating and managing expense categories.

Allows users to add, rename, and delete expense categories used for organizing
transactions throughout the application.
"""

from __future__ import annotations

from nicegui import ui
from ...domain.services import BudgetService
from ...domain.auth_service import AuthService


def categories_page(service: BudgetService, auth_service: AuthService) -> None:
    """Render the categories management page.
    
    Provides interface for CRUD operations on expense categories.
    
    Args:
        service (BudgetService): Application service for data access.
    """
    current_user = auth_service.current_user
    if not current_user:
        ui.label("Please log in to manage categories").classes("text-center mt-4")
        return
    user_id = current_user.id
    
    with ui.element('div').classes('page-wrap'):
        ui.label('Categories').classes('section-title')
        ui.label('Add, rename, and delete categories.').classes('muted mt-2')

        with ui.row().classes('w-full gap-3 mt-4 items-end'):
            name_in = ui.input(label='New category name').props('outlined dense').classes('w-full md:w-96')
            ui.button('Add', on_click=lambda: add_category_handler()).classes('')

        table = ui.table(
            columns=[
                {"name": "name", "label": "Name", "field": "name", "sortable": True},
                {"name": "actions", "label": "Actions", "field": "actions"},
            ],
            rows=[],
            row_key='id',
        ).classes('w-full mt-6').props('dense')

        def refresh() -> None:
            """Refresh the categories table."""
            rows = []
            for c in service.list_categories(user_id):
                rows.append({"id": c.id, "name": c.name, "actions": ""})
            table.rows = rows
            table.update()

        def add_category_handler() -> None:
            """Handle adding a new category."""
            n = (name_in.value or '').strip()
            if not n:
                ui.notify('Please enter a name', type='warning')
                return
            service.add_category(user_id, n)
            name_in.value = ''
            refresh()
            ui.notify('Category added')

        def rename_handler(row: dict) -> None:
            """Handle renaming a category."""
            category_id = int(row["id"])
            category_name = row["name"]
            
            # Create dialog for rename
            with ui.dialog() as rename_dialog, ui.card().classes('w-full max-w-sm'):
                ui.label(f'Rename Category: {category_name}').classes('text-lg font-semibold')
                ui.separator()
                new_name_input = ui.input(label='New name', value=category_name).props('outlined dense').classes('w-full mt-3')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancel', on_click=rename_dialog.close).props('flat')
                    ui.button('Rename', on_click=lambda: do_rename()).props('unelevated')
            
            def do_rename() -> None:
                new_name = (new_name_input.value or '').strip()
                if not new_name:
                    ui.notify('Please enter a name', type='warning')
                    return
                if new_name == category_name:
                    rename_dialog.close()
                    return
                service.rename_category(user_id, category_id, new_name)
                rename_dialog.close()
                refresh()
                ui.notify('Category renamed')
            
            rename_dialog.open()

        def delete_handler(row: dict) -> None:
            """Handle deleting a category."""
            category_id = int(row["id"])
            category_name = row["name"]
            
            # Confirmation dialog
            with ui.dialog() as confirm_dialog, ui.card().classes('w-full max-w-sm'):
                ui.label('Confirm Delete').classes('text-lg font-semibold text-red-600')
                ui.separator()
                ui.label(f'Are you sure you want to delete "{category_name}"?').classes('text-base')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancel', on_click=confirm_dialog.close).props('flat')
                    ui.button('Delete', on_click=lambda: do_delete()).props('unelevated color=negative')
            
            def do_delete() -> None:
                service.delete_category(user_id, category_id)
                confirm_dialog.close()
                refresh()
                ui.notify('Category deleted')
            
            confirm_dialog.open()

        # Action buttons slot
        table.add_slot(
            'body-cell-actions',
            '''
            <q-td :props="props">
              <div class="row items-center q-gutter-sm">
                <q-btn flat dense icon="edit" @click="$parent.$emit('edit_row', props.row)" />
                <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('delete_row', props.row)" />
              </div>
            </q-td>
            '''
        )
        
        # Wire table events to handlers
        table.on('edit_row', lambda e: rename_handler(e.args))
        table.on('delete_row', lambda e: delete_handler(e.args))

        refresh()
