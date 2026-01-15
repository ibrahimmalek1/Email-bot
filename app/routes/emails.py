"""
API routes for email operations
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import hashlib
from typing import Optional

from app.config import IMAPConfig, save_config, load_config, config_exists
from app.models.email import (
    EmailSummary, EmailSummaryResponse, EmailListResponse, 
    FetchEmailsRequest, ConfigResponse, FilterEmailsRequest
)
from app.services.imap_service import fetch_emails_with_config
from app.services.gmail_service import fetch_gmail_emails
from app.services.gemini_service import summarize_and_classify_email, is_gemini_configured
from app.services import storage
from app.services import oauth_service

router = APIRouter(prefix="/emails", tags=["Emails"])


# ==================== IMAP CONFIGURATION ====================

@router.post("/config", response_model=ConfigResponse)
async def configure_imap(config: IMAPConfig):
    """
    Configure IMAP settings for custom domain email fetching.
    """
    try:
        save_config(config)
        return ConfigResponse(
            success=True,
            message="IMAP configuration saved successfully",
            configured=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


@router.get("/config/status", response_model=ConfigResponse)
async def get_config_status():
    """Check if IMAP is configured"""
    is_configured = config_exists()
    return ConfigResponse(
        success=True,
        message="IMAP configured" if is_configured else "IMAP not configured",
        configured=is_configured
    )


# ==================== FETCH EMAILS ====================

@router.post("/fetch", response_model=EmailListResponse)
async def fetch_imap_and_summarize(request: FetchEmailsRequest = None):
    """
    Fetch emails via IMAP (for custom domains) with AI summarization.
    
    If Gemini is configured, emails will be:
    - Summarized with AI (one-line actionable summary)
    - Auto-categorized (Primary/Social/Promotions/Updates)
    - Prioritized (High/Medium/Low)
    """
    if request is None:
        request = FetchEmailsRequest()
    
    config = load_config()
    if not config:
        raise HTTPException(status_code=400, detail="IMAP not configured. POST to /emails/config first.")
    
    try:
        raw_emails = fetch_emails_with_config(config, limit=request.limit, days_back=request.days_back)
        
        if not raw_emails:
            return EmailListResponse(success=True, total=0, data=[])
        
        summaries = _process_emails_with_ai(raw_emails)
        storage.save_summaries_batch(summaries)
        
        return EmailListResponse(success=True, total=len(summaries), data=summaries)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@router.post("/fetch/gmail", response_model=EmailListResponse)
async def fetch_gmail_and_summarize(request: FetchEmailsRequest = None):
    """
    Fetch Gmail emails with AI summarization.
    
    ⭐ Uses Gemini AI for smart summaries if configured!
    
    Features (when Gemini is enabled):
    - One-line actionable summaries
    - Auto-categorization (Primary/Social/Promotions)
    - Priority detection (High/Medium/Low)
    - Action required detection
    """
    if request is None:
        request = FetchEmailsRequest()
    
    if not oauth_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /auth/login first.")
    
    new_summaries = []
    current_page_token = request.page_token
    max_pages = 10  # Safety limit: scan up to 10 pages (e.g. 500 emails) to find new ones
    pages_scanned = 0
    
    try:
        while len(new_summaries) < request.limit and pages_scanned < max_pages:
            result = fetch_gmail_emails(
                limit=request.limit, 
                days_back=request.days_back,
                page_token=current_page_token
            )
            
            raw_emails = result.get('emails', [])
            current_page_token = result.get('next_page_token')
            pages_scanned += 1
            
            if not raw_emails:
                break
            
            # Process and filter duplicates
            batch_summaries = _process_emails_with_ai(raw_emails)
            storage.save_summaries_batch(batch_summaries)
            new_summaries.extend(batch_summaries)
            
            # If no next page, stop
            if not current_page_token:
                break
        
        return EmailListResponse(
            success=True, 
            total=len(new_summaries), 
            data=new_summaries,
            next_page_token=current_page_token
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Gmail: {str(e)}")


# ==================== SUMMARIES WITH FILTERING ====================

@router.get("/summaries", response_model=EmailListResponse)
async def get_all_summaries(
    category: Optional[str] = Query(None, description="Filter by category: primary/social/promotions/updates"),
    priority: Optional[str] = Query(None, description="Filter by priority: high/medium/low"),
    sender_type: Optional[str] = Query(None, description="Filter by sender: person/company/newsletter/automated"),
    action_required: Optional[bool] = Query(None, description="Filter by action required"),
    has_attachments: Optional[bool] = Query(None, description="Filter by has attachments"),
    date_range: Optional[str] = Query(None, description="Filter by date: today/week/month"),
    search: Optional[str] = Query(None, description="Search in subject/sender/summary"),
    limit: Optional[int] = Query(None, description="Limit number of results (e.g., 5, 10, 20)")
):
    """
    Get all stored email summaries with smart filtering.
    
    Filters:
    - category: primary, social, promotions, updates
    - priority: high, medium, low
    - sender_type: person, company, newsletter, automated
    - action_required: true/false
    - has_attachments: true/false
    - date_range: today, week, month
    - search: text search in subject/sender/summary
    """
    summaries = storage.get_all_summaries()
    
    # Apply filters
    filters_applied = {}
    
    if category:
        summaries = [s for s in summaries if s.category == category.lower()]
        filters_applied["category"] = category
    
    if priority:
        summaries = [s for s in summaries if s.priority == priority.lower()]
        filters_applied["priority"] = priority
    
    if sender_type:
        summaries = [s for s in summaries if s.sender_type == sender_type.lower()]
        filters_applied["sender_type"] = sender_type
    
    if action_required is not None:
        summaries = [s for s in summaries if s.action_required == action_required]
        filters_applied["action_required"] = action_required
    
    if has_attachments is not None:
        summaries = [s for s in summaries if s.has_attachments == has_attachments]
        filters_applied["has_attachments"] = has_attachments
    
    if date_range:
        now = datetime.now()
        if date_range == "today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "week":
            cutoff = now - timedelta(days=7)
        elif date_range == "month":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = None
        
        if cutoff:
            # Make comparison safe by converting to naive datetime
            filtered = []
            for s in summaries:
                try:
                    email_date = s.date.replace(tzinfo=None) if s.date.tzinfo else s.date
                    if email_date >= cutoff:
                        filtered.append(s)
                except:
                    filtered.append(s)  # Include if date comparison fails
            summaries = filtered
            filters_applied["date_range"] = date_range
    
    if search:
        search_lower = search.lower()
        summaries = [
            s for s in summaries 
            if search_lower in s.subject.lower() 
            or search_lower in s.sender.lower()
            or search_lower in s.summary.lower()
        ]
        filters_applied["search"] = search
    
    # Apply limit (after all other filters)
    total_before_limit = len(summaries)
    if limit and limit > 0:
        summaries = summaries[:limit]
        filters_applied["limit"] = limit
    
    return EmailListResponse(
        success=True, 
        total=total_before_limit,  # Show total matching, not limited
        data=summaries,
        filters_applied=filters_applied if filters_applied else None
    )


@router.get("/summaries/stats")
async def get_summary_stats():
    """
    Get statistics about stored emails.
    
    Returns counts by category, priority, and action required.
    """
    summaries = storage.get_all_summaries()
    
    stats = {
        "total": len(summaries),
        "by_category": {},
        "by_priority": {},
        "by_sender_type": {},
        "action_required": 0,
        "with_attachments": 0
    }
    
    for s in summaries:
        # Category counts
        cat = s.category
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        
        # Priority counts
        pri = s.priority
        stats["by_priority"][pri] = stats["by_priority"].get(pri, 0) + 1
        
        # Sender type counts
        st = s.sender_type
        stats["by_sender_type"][st] = stats["by_sender_type"].get(st, 0) + 1
        
        # Action required
        if s.action_required:
            stats["action_required"] += 1
        
        # Attachments
        if s.has_attachments:
            stats["with_attachments"] += 1
    
    return stats


@router.get("/summaries/{summary_id}", response_model=EmailSummaryResponse)
async def get_summary(summary_id: str):
    """Get a specific email summary by ID"""
    summary = storage.get_summary_by_id(summary_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return EmailSummaryResponse(success=True, data=summary)


@router.delete("/summaries/{summary_id}", response_model=ConfigResponse)
async def delete_summary(summary_id: str):
    """Delete a specific email summary"""
    deleted = storage.delete_summary(summary_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return ConfigResponse(success=True, message="Summary deleted", configured=True)


@router.delete("/summaries", response_model=ConfigResponse)
async def clear_summaries():
    """Clear all stored summaries"""
    storage.clear_all_summaries()
    return ConfigResponse(success=True, message="All summaries cleared", configured=True)


# ==================== HELPER FUNCTIONS ====================

def _process_emails_with_ai(raw_emails: list) -> list:
    """Process raw emails with AI summarization and classification"""
    summaries = []
    
    for email_data in raw_emails:
        # Generate ID deterministically
        id_content = f"{email_data['subject']}{email_data['sender']}{email_data['date']}"
        email_id = hashlib.md5(id_content.encode()).hexdigest()[:12]
        
        # SKIP if already exists to save AI tokens and time
        if storage.check_email_exists(email_id):
            continue
            
        try:
            # Use Gemini AI for summarization and classification
            ai_result = summarize_and_classify_email(
                subject=email_data.get('subject', ''),
                sender=email_data.get('sender', ''),
                body=email_data.get('body', ''),
                has_attachments=email_data.get('has_attachments', False)
            )
            
            summary = EmailSummary(
                id=email_id,
                subject=email_data['subject'],
                sender=email_data['sender'],
                recipient=email_data.get('recipient', ''),
                date=email_data['date'],
                summary=ai_result['summary'],
                original_body=email_data.get('body', '')[:500] if email_data.get('body') else None,
                fetched_at=datetime.now(),
                # AI classification fields
                category=ai_result['category'],
                priority=ai_result['priority'],
                sender_type=ai_result['sender_type'],
                action_required=ai_result['action_required'],
                action_deadline=ai_result.get('action_deadline'),
                has_attachments=email_data.get('has_attachments', False)
            )
            summaries.append(summary)
            print(f"Summarized: {email_data['subject'][:30]}...")
            
        except Exception as e:
            print(f"Error processing email {email_id}: {e}")
            continue
    
    return summaries
