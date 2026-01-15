"""
Local JSON storage service for email summaries
"""
import json
import os
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.email import EmailSummary

STORAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "summaries.json")


def _ensure_storage_dir():
    """Ensure the data directory exists"""
    os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)


def _load_summaries() -> List[dict]:
    """Load all summaries from storage file"""
    if not os.path.exists(STORAGE_FILE):
        return []
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_summaries(summaries: List[dict]) -> None:
    """Save summaries to storage file"""
    _ensure_storage_dir()
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, default=str)


def clear_all_summaries() -> bool:
    """Clear all stored summaries"""
    try:
        print("Storage: Clearing all summaries...")
        _save_summaries([])
        print("Storage: Summaries cleared successfully.")
        return True
    except Exception as e:
        print(f"Error clearing summaries: {e}")
        return False


def save_summary(summary: EmailSummary) -> bool:
    """
    Save a single email summary to storage
    
    Args:
        summary: EmailSummary object to save
        
    Returns:
        True if saved successfully
    """
    try:
        summaries = _load_summaries()
        
        # Check if summary with this ID already exists
        existing_ids = {s.get('id') for s in summaries}
        if summary.id in existing_ids:
            # Update existing
            summaries = [s if s.get('id') != summary.id else summary.model_dump() 
                        for s in summaries]
        else:
            # Add new
            summaries.append(summary.model_dump())
        
        _save_summaries(summaries)
        return True
    except Exception as e:
        print(f"Error saving summary: {e}")
        return False


def save_summaries_batch(summaries_list: List[EmailSummary]) -> int:
    """
    Save multiple summaries at once
    
    Args:
        summaries_list: List of EmailSummary objects
        
    Returns:
        Number of summaries saved
    """
    try:
        existing = _load_summaries()
        existing_ids = {s.get('id') for s in existing}
        
        new_count = 0
        for summary in summaries_list:
            if summary.id not in existing_ids:
                existing.append(summary.model_dump())
                existing_ids.add(summary.id)
                new_count += 1
        
        _save_summaries(existing)
        return new_count
    except Exception as e:
        print(f"Error saving summaries: {e}")
        return 0


def get_all_summaries() -> List[EmailSummary]:
    """Get all stored email summaries"""
    summaries = _load_summaries()
    return [EmailSummary(**s) for s in summaries]


def get_summaries_by_date(target_date: str) -> List[dict]:
    """
    Get summaries filtered by a specific date (YYYY-MM-DD)
    
    Args:
        target_date: Date string in YYYY-MM-DD format
        
    Returns:
        List of summary dicts for that date
    """
    summaries = _load_summaries()
    result = []
    
    for s in summaries:
        # parsed_date string format example: "2026-01-04 22:06:53-08:00"
        date_str = s.get('date')
        if not date_str:
            continue
            
        try:
            # Simple string matching for the date part usually works if format is consistent
            # But let's be robust and parse it
            # Using basic string slicing for "YYYY-MM-DD" matching is faster/easier if format is reliable
            # "2026-01-04..."
            if date_str.startswith(target_date):
                result.append(s)
        except Exception:
            continue
            
    return result


def get_filtered_summaries(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    sender_type: Optional[str] = None,
    action_required: Optional[bool] = None,
    has_attachments: Optional[bool] = None,
    date_range: Optional[str] = None,
    search: Optional[str] = None
) -> List[EmailSummary]:
    """Get summaries with filters applied"""
    summaries = get_all_summaries()
    
    if category:
        summaries = [s for s in summaries if s.category == category.lower()]
    
    if priority:
        summaries = [s for s in summaries if s.priority == priority.lower()]
    
    if sender_type:
        summaries = [s for s in summaries if s.sender_type == sender_type.lower()]
    
    if action_required is not None:
        summaries = [s for s in summaries if s.action_required == action_required]
        
    # Always sort by date descending (Newest First)
    summaries.sort(key=lambda x: x.date, reverse=True)
    
    if has_attachments is not None:
        summaries = [s for s in summaries if s.has_attachments == has_attachments]
    
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
            filtered = []
            for s in summaries:
                try:
                    email_date = s.date.replace(tzinfo=None) if s.date.tzinfo else s.date
                    if email_date >= cutoff:
                        filtered.append(s)
                except:
                    filtered.append(s)
            summaries = filtered
    
    if search:
        search_lower = search.lower()
        search_terms = search_lower.split()
        
        filtered = []
        for s in summaries:
            # Combine fields for search
            text = f"{s.subject} {s.sender} {s.summary}".lower()
            if all(term in text for term in search_terms):
                filtered.append(s)
        summaries = filtered
        
    return summaries


def get_summary_by_id(summary_id: str) -> Optional[EmailSummary]:
    """Get a specific summary by ID"""
    summaries = _load_summaries()
    
    for s in summaries:
        if s.get('id') == summary_id:
            try:
                if isinstance(s.get('date'), str):
                    s['date'] = datetime.fromisoformat(s['date'].replace('Z', '+00:00'))
                if isinstance(s.get('fetched_at'), str):
                    s['fetched_at'] = datetime.fromisoformat(s['fetched_at'].replace('Z', '+00:00'))
                return EmailSummary(**s)
            except:
                return None
    
    return None


def delete_summary(summary_id: str) -> bool:
    """Delete a summary by ID"""
    try:
        summaries = _load_summaries()
        original_count = len(summaries)
        
        summaries = [s for s in summaries if s.get('id') != summary_id]
        
        if len(summaries) < original_count:
            _save_summaries(summaries)
            return True
        return False
    except:
        return False


def clear_all_summaries() -> bool:
    """Clear all stored summaries"""
    try:
        print("Storage: Clearing all summaries...")
        _save_summaries([])
        print("Storage: Summaries cleared successfully")
        return True
    except Exception as e:
        print(f"Storage: Error clearing summaries: {e}")
        return False


def check_email_exists(email_id: str) -> bool:
    """Check if an email ID already exists in storage"""
    summaries = _load_summaries()
    return any(s.get('id') == email_id for s in summaries)
