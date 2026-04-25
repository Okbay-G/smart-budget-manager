"""User authentication page with login and registration interface.

Provides a centered, professional login/signup form allowing users to register
new accounts and authenticate before accessing the application.
"""

from __future__ import annotations

from nicegui import ui
from ...services.auth_service import AuthService


def auth_page(auth_service: AuthService) -> None:
    """Render the authentication page with login and signup forms.
    
    Provides unified login/signup interface with centered, aesthetic design.
    Users can toggle between login and signup modes.
    
    Args:
        auth_service (AuthService): Authentication service for login/signup.
    """
    # If already logged in, redirect to dashboard
    if auth_service.is_logged_in():
        ui.navigate.to('/')
        return
    
    # Add custom CSS for auth page
    ui.add_head_html("""
        <style>
            .auth-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .auth-card {
                width: 100%;
                max-width: 420px;
                padding: 40px;
                border-radius: 16px;
                background: white;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            .auth-header {
                text-align: center;
                margin-bottom: 32px;
            }
            .auth-title {
                font-size: 32px;
                font-weight: 800;
                color: #1f2937;
                margin: 0;
                margin-bottom: 8px;
            }
            .auth-subtitle {
                font-size: 14px;
                color: #6b7280;
            }
            .auth-form {
                display: flex;
                flex-direction: column;
                gap: 16px;
            }
            .auth-tabs {
                display: flex;
                gap: 12px;
                margin-bottom: 24px;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 16px;
            }
            .auth-tab-btn {
                flex: 1;
                padding: 12px 16px;
                border: none;
                background: none;
                color: #6b7280;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                border-bottom: 3px solid transparent;
                margin-bottom: -19px;
            }
            .auth-tab-btn.active {
                color: #667eea;
                border-bottom-color: #667eea;
            }
            .auth-input {
                padding: 12px 16px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s ease;
            }
            .auth-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .auth-button {
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
            }
            .auth-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            .auth-button:active {
                transform: translateY(0);
            }
            .auth-message {
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 14px;
                text-align: center;
            }
            .auth-message.error {
                background: #fee;
                color: #c33;
                border: 1px solid #fcc;
            }
            .auth-message.success {
                background: #efe;
                color: #3c3;
                border: 1px solid #cfc;
            }
            .auth-footer {
                text-align: center;
                margin-top: 24px;
                color: #6b7280;
                font-size: 13px;
            }
        </style>
    """)
    
    # Main auth container
    with ui.element('div').classes('auth-container').style('width: 100%; height: 100vh'):
        with ui.element('div').classes('auth-card'):
            # Header
            with ui.element('div').classes('auth-header'):
                ui.label('Budget Manager').classes('auth-title')
                ui.label('Manage your finances with ease').classes('auth-subtitle')
            
            # State management
            mode = {'current': 'login'}
            
            # Mode tabs
            with ui.element('div').classes('auth-tabs'):
                def set_mode_login():
                    mode['current'] = 'login'
                    update_ui()
                
                def set_mode_signup():
                    mode['current'] = 'signup'
                    update_ui()
                
                login_tab = ui.button('Login').props('flat').classes('auth-tab-btn active').on_click(set_mode_login)
                signup_tab = ui.button('Sign Up').props('flat').classes('auth-tab-btn').on_click(set_mode_signup)
            
            # Form
            with ui.element('div').classes('auth-form'):
                email_input = ui.input(
                    placeholder='Email Address'
                ).props('outlined').classes('auth-input').style('width: 100%')
                
                username_input = ui.input(
                    placeholder='Username (optional)'
                ).props('outlined').classes('auth-input').style('width: 100%')
                
                password_input = ui.input(
                    placeholder='Password',
                ).props('outlined type=password').classes('auth-input').style('width: 100%')
                
                confirm_password_input = ui.input(
                    placeholder='Confirm Password'
                ).props('outlined type=password').classes('auth-input').style('width: 100%')
                
                # Messages
                error_label = ui.label('').classes('auth-message error').style('display: none')
                success_label = ui.label('').classes('auth-message success').style('display: none')
                
                # Submit button
                submit_button = ui.button('Login').props('flat').classes('auth-button')
            
            # Footer
            ui.label('Secure & Private').classes('auth-footer')
        
        def update_ui():
            """Update UI based on current mode."""
            if mode['current'] == 'signup':
                login_tab.props('flat').classes(remove='active')
                signup_tab.props('flat').classes(add='active')
                username_input.visible = True
                confirm_password_input.visible = True
                submit_button.text = 'Create Account'
            else:
                login_tab.props('flat').classes(add='active')
                signup_tab.props('flat').classes(remove='active')
                username_input.visible = False
                confirm_password_input.visible = False
                submit_button.text = 'Login'
        
        def show_error(message: str):
            """Show error message."""
            error_label.text = message
            error_label.style('display: block')
            success_label.style('display: none')
        
        def show_success(message: str):
            """Show success message."""
            success_label.text = message
            success_label.style('display: block')
            error_label.style('display: none')
        
        def clear_messages():
            """Clear all messages."""
            error_label.style('display: none')
            success_label.style('display: none')
        
        def handle_submit():
            """Handle form submission."""
            clear_messages()
            
            if mode['current'] == 'login':
                handle_login()
            else:
                handle_signup()
        
        def handle_login():
            """Handle login."""
            email = (email_input.value or '').strip()
            password = (password_input.value or '').strip()
            
            if not email or not password:
                show_error('Email and password required')
                return
            
            success, message = auth_service.login(email, password)
            if success:
                show_success('Login successful, redirecting...')
                # Clear inputs after successful login
                email_input.value = ''
                password_input.value = ''
                ui.timer(1.0, lambda: ui.navigate.to('/'))
            else:
                show_error(message)
        
        def handle_signup():
            """Handle signup."""
            email = (email_input.value or '').strip()
            username = (username_input.value or '').strip()
            password = (password_input.value or '').strip()
            confirm = (confirm_password_input.value or '').strip()
            
            if not email or not password:
                show_error('Email and password are required')
                return
            
            if password != confirm:
                show_error('Passwords do not match')
                return
            
            success, message = auth_service.register(email, password, username)
            if success:
                show_success(message + '. You can now login!')
                # Clear inputs
                username_input.value = ''
                password_input.value = ''
                confirm_password_input.value = ''
                email_input.value = ''
                # Switch to login after 2 seconds
                ui.timer(2, lambda: (update_ui(), mode.update({'current': 'login'})))
            else:
                show_error(message)
        
        # Wire submit button
        submit_button.on_click(handle_submit)
        
        # Initial UI setup (login mode by default)
        username_input.visible = False
        confirm_password_input.visible = False
