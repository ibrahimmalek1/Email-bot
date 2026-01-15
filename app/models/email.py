"""
Pydantic models for email data
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class EmailCategory(str, Enum):
    PRIMARY = "primary"
    SOCIAL = "social"
    PROMOTIONS = "promotions"
    UPDATES = "updates"
    FORUMS = "forums"


class EmailPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SenderType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    NEWSLETTER = "newsletter"
    AUTOMATED = "automated"


class EmailSummary(BaseModel):
    """Model for a summarized email with AI classification"""
    id: str
    subject: str
    sender: str
    recipient: str
    date: datetime
    summary: str  # AI-generated summary
    original_body: Optional[str] = None
    fetched_at: datetime
    
    # AI Classification fields
    category: str = "primary"  # primary/social/promotions/updates/forums
    priority: str = "medium"   # high/medium/low
    sender_type: str = "company"  # person/company/newsletter/automated
    action_required: bool = False
    action_deadline: Optional[str] = None
    has_attachments: bool = False


class EmailSummaryResponse(BaseModel):
    """Response model for a single email summary"""
    success: bool
    data: Optional[EmailSummary] = None
    message: Optional[str] = None


class EmailListResponse(BaseModel):
    """Response model for list of email summaries"""
    success: bool
    total: int
    data: List[EmailSummary]
    # Filter stats
    filters_applied: Optional[dict] = None
    next_page_token: Optional[str] = None


class FetchEmailsRequest(BaseModel):
    """Request model for fetching emails"""
    limit: int = 10
    days_back: int = 7
    page_token: Optional[str] = None


class FilterEmailsRequest(BaseModel):
    """Request model for filtering summaries"""
    category: Optional[str] = None  # primary/social/promotions/updates
    priority: Optional[str] = None  # high/medium/low
    sender_type: Optional[str] = None  # person/company/newsletter/automated
    action_required: Optional[bool] = None
    has_attachments: Optional[bool] = None
    date_range: Optional[str] = None  # today/week/month
    search: Optional[str] = None  # Search in subject/sender/summary


class ConfigResponse(BaseModel):
    """Response for configuration operations"""
    success: bool
    message: str
    configured: bool = False


class GeminiConfigRequest(BaseModel):
    """Request for Gemini API key configuration"""
    api_key: str
