"""
Gmail API integration
Handles email reading, summarization, sending, and UI handoff
"""
from typing import Dict, Any, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import base64
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)


class GmailService:
    """Gmail API service handler"""
    
    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail service
        
        Args:
            credentials: Google OAuth2 credentials
        """
        self.service = build('gmail', 'v1', credentials=credentials)
    
    async def get_recent_emails(
        self,
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent emails
        
        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query (e.g., 'is:important')
        
        Returns:
            List of email summaries
        """
        try:
            # Build query
            search_query = query or "is:unread"
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            # Fetch full message details
            email_list = []
            for msg in messages:
                email_data = await self._get_email_details(msg['id'])
                if email_data:
                    email_list.append(email_data)
            
            return email_list
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
    
    async def _get_email_details(self, message_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific email
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Email details dictionary
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract key information
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get email body
            body = self._extract_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'from': sender,
                'date': date,
                'snippet': message.get('snippet', ''),
                'body': body[:500]  # First 500 chars
            }
            
        except HttpError as error:
            logger.error(f"Error fetching email {message_id}: {error}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Fallback to body data
        data = payload.get('body', {}).get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return ""
    
    async def send_reply(
        self,
        message_id: str,
        reply_text: str
    ) -> Dict[str, Any]:
        """
        Send a reply to an email
        
        Args:
            message_id: Original message ID to reply to
            reply_text: Reply content
        
        Returns:
            Sent message details
        """
        try:
            # Get original message for threading
            original = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = original['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            to = next((h['value'] for h in headers if h['name'] == 'From'), '')
            thread_id = original['threadId']
            
            # Add Re: if not present
            if not subject.startswith('Re:'):
                subject = f"Re: {subject}"
            
            # Create message
            message = MIMEText(reply_text)
            message['to'] = to
            message['subject'] = subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send reply
            sent_message = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': thread_id
                }
            ).execute()
            
            return {
                'id': sent_message['id'],
                'thread_id': sent_message['threadId'],
                'status': 'sent'
            }
            
        except HttpError as error:
            logger.error(f"Error sending reply: {error}")
            raise
    
    async def summarize_emails(
        self,
        emails: List[Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable summary of emails
        
        Args:
            emails: List of email dictionaries
        
        Returns:
            Summary text
        """
        if not emails:
            return "You have no new emails."
        
        summary_parts = [f"You have {len(emails)} email(s):"]
        
        for i, email in enumerate(emails[:5], 1):  # Limit to 5 for voice
            sender = email['from'].split('<')[0].strip()
            subject = email['subject']
            summary_parts.append(f"{i}. From {sender}: {subject}")
        
        return "\n".join(summary_parts)
    
    @staticmethod
    def generate_gmail_url(message_id: Optional[str] = None) -> str:
        """
        Generate Gmail web UI URL
        
        Args:
            message_id: Specific message ID (optional)
        
        Returns:
            Gmail URL
        """
        base_url = "https://mail.google.com/mail/u/0/"
        
        if message_id:
            return f"{base_url}#inbox/{message_id}"
        
        return f"{base_url}#inbox"
