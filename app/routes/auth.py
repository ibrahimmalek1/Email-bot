"""
OAuth Authentication Routes
Handles Google Sign-In flow
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from app.services import oauth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


class OAuthCredentials(BaseModel):
    """Google OAuth credentials from Google Cloud Console"""
    client_id: str
    client_secret: str


class AuthStatus(BaseModel):
    """Authentication status response"""
    authenticated: bool
    credentials_configured: bool
    user: Optional[dict] = None
    message: str


@router.post("/setup", response_model=AuthStatus)
async def setup_google_oauth(credentials: OAuthCredentials):
    """
    Configure Google OAuth credentials.
    
    Get these from Google Cloud Console:
    1. Go to https://console.cloud.google.com
    2. Create a project → Enable Gmail API
    3. Create OAuth 2.0 credentials
    4. Add redirect URI: http://localhost:8000/auth/callback
    """
    success = oauth_service.save_oauth_credentials(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret
    )
    
    if success:
        return AuthStatus(
            authenticated=False,
            credentials_configured=True,
            message="Google OAuth configured. Visit /auth/login to sign in."
        )
    raise HTTPException(status_code=500, detail="Failed to save Google credentials")


@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    """Check current authentication status"""
    is_configured = oauth_service.credentials_exist()
    is_authenticated = oauth_service.is_authenticated()
    user = oauth_service.get_user_info() if is_authenticated else None
    
    if not is_configured:
        message = "Google OAuth not configured. POST to /auth/setup first."
    elif not is_authenticated:
        message = "Not logged in. Visit /auth/login to sign in."
    else:
        message = f"Logged in as {user.get('email', 'unknown')}"
    
    return AuthStatus(
        authenticated=is_authenticated,
        credentials_configured=is_configured,
        user=user,
        message=message
    )


@router.get("/login")
async def google_login():
    """Start Google OAuth login flow."""
    if not oauth_service.credentials_exist():
        raise HTTPException(status_code=400, detail="Google OAuth not configured. POST to /auth/setup first.")
    
    auth_url = oauth_service.get_auth_url()
    if not auth_url:
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sign in with Google</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex; justify-content: center; align-items: center;
                height: 100vh; margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white; padding: 40px; border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; max-width: 400px;
            }}
            h1 {{ color: #333; margin-bottom: 20px; }}
            p {{ color: #666; margin-bottom: 30px; }}
            .btn {{
                display: inline-flex; align-items: center; padding: 14px 28px;
                background: #4285f4; color: white; text-decoration: none;
                border-radius: 8px; font-size: 16px; font-weight: 500;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(66,133,244,0.4); }}
            .btn img {{ width: 24px; height: 24px; margin-right: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📧 Email Summarizer</h1>
            <p>Sign in with your Google account to access your emails</p>
            <a href="{auth_url}" class="btn">
                <img src="https://www.google.com/favicon.ico" alt="Google">
                Sign in with Google
            </a>
        </div>
    </body>
    </html>
    """)


@router.get("/callback")
async def google_callback(code: str = None, error: str = None):
    """Google OAuth callback endpoint."""
    if error:
        return HTMLResponse(content=f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #fee;">
            <h1>❌ Authentication Failed</h1>
            <p style="color: #c00;">{error}</p>
            <a href="/auth/login" style="color: #4285f4;">Try Again</a>
        </body>
        </html>
        """)
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    result = oauth_service.handle_oauth_callback(code)
    
    if result["success"]:
        user = result.get("user", {})
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex; justify-content: center; align-items: center;
                    height: 100vh; margin: 0;
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                }}
                .container {{
                    background: white; padding: 40px; border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;
                }}
                .avatar {{ width: 80px; height: 80px; border-radius: 50%; margin-bottom: 20px; }}
                h1 {{ color: #333; }}
                p {{ color: #666; }}
                a {{
                    display: inline-block; margin-top: 20px; padding: 12px 24px;
                    background: #4285f4; color: white; text-decoration: none; border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <img src="{user.get('picture', 'https://via.placeholder.com/80')}" class="avatar" alt="Profile">
                <h1>✅ Welcome, {user.get('name', 'User')}!</h1>
                <p>Logged in as: {user.get('email', 'unknown')}</p>
                <p>You can now fetch and summarize your emails.</p>
                <a href="/docs">Go to API Docs</a>
            </div>
        </body>
        </html>
        """)
    else:
        return HTMLResponse(content=f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #fee;">
            <h1>❌ Authentication Failed</h1>
            <p style="color: #c00;">{result.get('error', 'Unknown error')}</p>
            <a href="/auth/login" style="color: #4285f4;">Try Again</a>
        </body>
        </html>
        """)


@router.post("/logout")
async def logout():
    """Logout - removes stored authentication token"""
    oauth_service.logout()
    return {"success": True, "message": "Logged out successfully"}
