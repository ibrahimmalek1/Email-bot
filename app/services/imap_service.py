"""
IMAP email fetching service
Connects to any IMAP server and fetches emails
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from app.config import IMAPConfig


class IMAPService:
    """Service to fetch emails via IMAP protocol"""
    
    def __init__(self, config: IMAPConfig):
        self.config = config
        self.connection: Optional[imaplib.IMAP4_SSL] = None
    
    def connect(self) -> bool:
        """Establish connection to IMAP server"""
        try:
            if self.config.use_ssl:
                self.connection = imaplib.IMAP4_SSL(
                    self.config.imap_server, 
                    self.config.imap_port
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.config.imap_server, 
                    self.config.imap_port
                )
            
            self.connection.login(self.config.email, self.config.password)
            return True
        except Exception as e:
            print(f"IMAP connection error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close IMAP connection"""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None
    
    def _decode_header_value(self, value: str) -> str:
        """Decode email header value (handles encoded subjects/names)"""
        if not value:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        
        return " ".join(decoded_parts)
    
    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract plain text body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break
                    except:
                        continue
                elif content_type == "text/html" and not body:
                    # Fallback to HTML if no plain text
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = payload.decode(charset, errors='replace')
                        # Basic HTML tag removal
                        body = re.sub(r'<[^>]+>', ' ', html_body)
                        body = re.sub(r'\s+', ' ', body).strip()
                    except:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
            except:
                body = str(msg.get_payload())
        
        return body.strip()
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string to datetime"""
        try:
            return parsedate_to_datetime(date_str)
        except:
            return datetime.now()
    
    def fetch_emails(self, limit: int = 10, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch emails from the configured mailbox
        
        Args:
            limit: Maximum number of emails to fetch
            days_back: Fetch emails from last N days
            
        Returns:
            List of email dictionaries with subject, sender, date, body
        """
        if not self.connection:
            if not self.connect():
                return []
        
        emails = []
        
        try:
            # Select mailbox
            self.connection.select(self.config.mailbox)
            
            # Search for emails from last N days
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            search_criteria = f'(SINCE "{since_date}")'
            
            status, message_ids = self.connection.search(None, search_criteria)
            
            if status != "OK":
                return []
            
            # Get message IDs (most recent first)
            id_list = message_ids[0].split()
            id_list = id_list[-limit:] if len(id_list) > limit else id_list
            id_list.reverse()  # Most recent first
            
            for msg_id in id_list:
                try:
                    status, msg_data = self.connection.fetch(msg_id, "(RFC822)")
                    
                    if status != "OK":
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    subject = self._decode_header_value(msg.get("Subject", "No Subject"))
                    sender = self._decode_header_value(msg.get("From", "Unknown"))
                    recipient = self._decode_header_value(msg.get("To", ""))
                    date = self._parse_date(msg.get("Date", ""))
                    body = self._get_email_body(msg)
                    
                    emails.append({
                        "message_id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                        "subject": subject,
                        "sender": sender,
                        "recipient": recipient,
                        "date": date,
                        "body": body
                    })
                    
                except Exception as e:
                    print(f"Error parsing email {msg_id}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
        
        return emails


def fetch_emails_with_config(config: IMAPConfig, limit: int = 10, 
                              days_back: int = 7) -> List[Dict[str, Any]]:
    """Convenience function to fetch emails with given config"""
    service = IMAPService(config)
    try:
        return service.fetch_emails(limit=limit, days_back=days_back)
    finally:
        service.disconnect()
