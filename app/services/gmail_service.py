"""
Gmail API Service - Uses OAuth to fetch emails
Alternative to IMAP that works with Google Sign-In
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
import re

from googleapiclient.discovery import build

from app.services.oauth_service import get_credentials, is_authenticated


class GmailService:
    """Service to fetch emails using Gmail API (OAuth)"""
    
    def __init__(self):
        self.service = None
    
    def connect(self) -> bool:
        """Connect to Gmail API using stored OAuth credentials"""
        credentials = get_credentials()
        if not credentials:
            return False
        
        try:
            self.service = build('gmail', 'v1', credentials=credentials)
            return True
        except Exception as e:
            print(f"Gmail API connection error: {e}")
            return False
    
    def _decode_body(self, payload: dict) -> str:
        """Extract and decode email body from Gmail API payload"""
        body = ""
        
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        
        elif 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    if part['body'].get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                        break
                elif mime_type == 'text/html' and not body:
                    if part['body'].get('data'):
                        html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                        
                        # Remove style and script blocks completely
                        html_body = re.sub(r'<style.*?>.*?</style>', '', html_body, flags=re.DOTALL | re.IGNORECASE)
                        html_body = re.sub(r'<script.*?>.*?</script>', '', html_body, flags=re.DOTALL | re.IGNORECASE)
                        
                        # Basic HTML tag removal
                        body = re.sub(r'<[^>]+>', ' ', html_body)
                        body = re.sub(r'\s+', ' ', body).strip()
                elif 'parts' in part:
                    # Nested parts (multipart)
                    body = self._decode_body(part)
                    if body:
                        break
        
        return body.strip()
    
    def _get_header(self, headers: list, name: str) -> str:
        """Get header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""
    
    def fetch_emails(self, limit: int = 10, days_back: int = 7, page_token: str = None) -> Dict[str, Any]:
        """
        Fetch emails using Gmail API
        
        Args:
            limit: Maximum number of emails to fetch
            days_back: Fetch emails from last N days
            page_token: Token for next page of results
            
        Returns:
            Dict containing 'emails' list and 'next_page_token'
        """
        if not self.service:
            if not self.connect():
                return {"emails": [], "next_page_token": None}
        
        emails = []
        next_token = None
        
        try:
            # Build query for recent emails
            query = f"newer_than:{days_back}d"
            
            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit,
                pageToken=page_token
            ).execute()
            
            messages = results.get('messages', [])
            next_token = results.get('nextPageToken')
            
            for msg_info in messages:
                try:
                    # Get full message
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=msg_info['id'],
                        format='full'
                    ).execute()
                    
                    headers = msg['payload'].get('headers', [])
                    
                    # Parse date
                    date_str = self._get_header(headers, 'Date')
                    try:
                        from email.utils import parsedate_to_datetime
                        date = parsedate_to_datetime(date_str)
                    except:
                        date = datetime.now()
                    
                    # Extract body
                    body = self._decode_body(msg['payload'])
                    
                    # Fallback to snippet if body extraction fails/is empty
                    if not body or len(body.strip()) < 10:
                        snippet = msg.get('snippet', '')
                        if snippet:
                            print(f"Using snippet for email {msg_info['id']} (Body empty/short)")
                            body = snippet

                    emails.append({
                        "message_id": msg_info['id'],
                        "subject": self._get_header(headers, 'Subject') or "No Subject",
                        "sender": self._get_header(headers, 'From') or "Unknown",
                        "recipient": self._get_header(headers, 'To') or "",
                        "date": date,
                        "body": body
                    })
                    
                except Exception as e:
                    print(f"Error parsing message {msg_info['id']}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
        
        return {"emails": emails, "next_page_token": next_token}


def fetch_gmail_emails(limit: int = 10, days_back: int = 7, page_token: str = None) -> Dict[str, Any]:
    """Convenience function to fetch Gmail emails using OAuth"""
    if not is_authenticated():
        return {"emails": [], "next_page_token": None}
    
    service = GmailService()
    return service.fetch_emails(limit=limit, days_back=days_back, page_token=page_token)
