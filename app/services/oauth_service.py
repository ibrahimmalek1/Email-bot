"""
Google OAuth 2.0 Authentication Service
Handles Google Sign-In flow for Gmail access
"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/userinfo.email',  # Get user email
    'https://www.googleapis.com/auth/userinfo.profile',  # Get user profile
    'openid'
]

# Paths for storing credentials
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "google_credentials.json")
TOKEN_FILE = os.path.join(DATA_DIR, "google_token.json")


def _ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_oauth_credentials(client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8000/auth/callback") -> bool:
    """
    Save Google OAuth credentials (Client ID & Secret)
    These are obtained from Google Cloud Console
    """
    try:
        _ensure_data_dir()
        credentials = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False


def credentials_exist() -> bool:
    """Check if OAuth credentials are configured"""
    return os.path.exists(CREDENTIALS_FILE)


def token_exists() -> bool:
    """Check if user has authenticated (token exists)"""
    return os.path.exists(TOKEN_FILE)


def get_auth_url() -> Optional[str]:
    """
    Generate Google OAuth authorization URL
    User visits this URL to sign in with Google
    """
    if not credentials_exist():
        return None
    
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/auth/callback"
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent select_account'
        )
        
        return auth_url
    except Exception as e:
        print(f"Error generating auth URL: {e}")
        return None


def handle_oauth_callback(authorization_code: str) -> Dict[str, Any]:
    """
    Handle OAuth callback after user authorizes
    Exchange authorization code for access token
    """
    if not credentials_exist():
        return {"success": False, "error": "OAuth credentials not configured"}
    
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/auth/callback"
        )
        
        # Exchange code for token
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials
        
        # Save token for future use
        _ensure_data_dir()
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes),
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        # Get user info
        user_info = get_user_info(credentials)
        
        return {
            "success": True,
            "message": "Successfully authenticated with Google",
            "user": user_info
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_credentials() -> Optional[Credentials]:
    """
    Get valid Google credentials
    Refreshes token if expired
    """
    if not token_exists():
        return None
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        
        credentials = Credentials(
            token=token_data['token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Save refreshed token
            token_data['token'] = credentials.token
            token_data['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f, indent=2)
        
        return credentials
        
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None


def get_user_info(credentials: Credentials = None) -> Optional[Dict[str, str]]:
    """Get authenticated user's email and profile info"""
    if credentials is None:
        credentials = get_credentials()
    
    if credentials is None:
        return None
    
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return {
            "email": user_info.get('email'),
            "name": user_info.get('name'),
            "picture": user_info.get('picture')
        }
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None


def logout() -> bool:
    """Remove stored token (logout user)"""
    try:
        print("OAuth: Logout called - deleting token file...")
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print(f"OAuth: Token file deleted: {TOKEN_FILE}")
        else:
            print("OAuth: No token file to delete")
        
        # Also delete summaries file to ensure clean slate
        summaries_file = os.path.join(DATA_DIR, "summaries.json")
        if os.path.exists(summaries_file):
            os.remove(summaries_file)
            print(f"OAuth: Summaries file deleted: {summaries_file}")
            
        return True
    except Exception as e:
        print(f"OAuth: Logout error: {e}")
        return False


def is_authenticated() -> bool:
    """Check if user is authenticated with valid token"""
    credentials = get_credentials()
    return credentials is not None and credentials.valid
