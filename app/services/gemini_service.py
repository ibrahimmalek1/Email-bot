"""
Google Gemini AI Service
Handles AI summarization and email classification
"""
import os
import json
from typing import Optional, Dict, Any
from enum import Enum

import google.generativeai as genai

# Paths for storing API key
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GEMINI_CONFIG_FILE = os.path.join(DATA_DIR, "gemini_config.json")


class EmailCategory(str, Enum):
    PRIMARY = "primary"
    SOCIAL = "social"
    PROMOTIONS = "promotions"
    UPDATES = "updates"
    FORUMS = "forums"
    SPAM = "spam"


class EmailPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SenderType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    NEWSLETTER = "newsletter"
    AUTOMATED = "automated"


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_gemini_api_key(api_key: str) -> bool:
    """Save Gemini API key to local config"""
    try:
        _ensure_data_dir()
        with open(GEMINI_CONFIG_FILE, 'w') as f:
            json.dump({"api_key": api_key}, f)
        return True
    except Exception as e:
        print(f"Error saving Gemini API key: {e}")
        return False


def get_gemini_api_key() -> Optional[str]:
    """Get stored Gemini API key"""
    if not os.path.exists(GEMINI_CONFIG_FILE):
        return None
    try:
        with open(GEMINI_CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return data.get("api_key")
    except:
        return None


def is_gemini_configured() -> bool:
    """Check if Gemini API key is configured"""
    return get_gemini_api_key() is not None


def _get_gemini_model():
    """Initialize and return Gemini model"""
    api_key = get_gemini_api_key()
    if not api_key:
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-3-flash-preview')


def summarize_and_classify_email(
    subject: str,
    sender: str,
    body: str,
    has_attachments: bool = False
) -> Dict[str, Any]:
    """
    Use Gemini AI to summarize and classify an email.
    
    Returns dict with:
    - summary: One-line actionable summary
    - category: primary/social/promotions/updates/forums
    - priority: high/medium/low
    - sender_type: person/company/newsletter/automated
    - action_required: bool
    - action_deadline: str or None
    """
    model = _get_gemini_model()
    
    if not model:
        # Fallback to basic summary if Gemini not configured
        return _fallback_classification(subject, sender, body)
    
    # Truncate body to save tokens
    truncated_body = body[:2000] if body else ""
    
    prompt = f"""Analyze this email and provide a JSON response:

SUBJECT: {subject}
FROM: {sender}
BODY: {truncated_body}
HAS ATTACHMENTS: {has_attachments}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
    "summary": "One concise sentence summarizing the email and any action needed",
    "category": "primary" or "social" or "promotions" or "updates" or "forums",
    "priority": "high" or "medium" or "low",
    "sender_type": "person" or "company" or "newsletter" or "automated",
    "action_required": true or false,
    "action_deadline": "date string if mentioned, otherwise null"
}}

Rules:
- summary: Max 100 chars, highlight key info (dates, amounts, names)
- priority HIGH if: urgent, deadline, money, important person
- priority LOW if: newsletter, promotion, automated notification
- action_required: true if user needs to respond/do something"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Validate and normalize
        return {
            "summary": result.get("summary", subject)[:1000],
            "category": result.get("category", "primary").lower(),
            "priority": result.get("priority", "medium").lower(),
            "sender_type": result.get("sender_type", "company").lower(),
            "action_required": bool(result.get("action_required", False)),
            "action_deadline": result.get("action_deadline")
        }
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_classification(subject, sender, body)


def _fallback_classification(subject: str, sender: str, body: str) -> Dict[str, Any]:
    """Basic classification when Gemini is not available"""
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    
    # DEBUG LOGGING
    print(f"Fallback Classification - Subject: {subject[:30]}..., Body Len: {len(body) if body else 0}")
    
    # Basic category detection
    category = "primary"
    if any(word in sender_lower for word in ["newsletter", "news@", "updates@", "noreply"]):
        category = "updates"
    elif any(word in subject_lower for word in ["sale", "offer", "discount", "%off", "deal"]):
        category = "promotions"
    elif any(word in sender_lower for word in ["facebook", "twitter", "linkedin", "instagram"]):
        category = "social"
    
    # Basic priority detection
    priority = "medium"
    if any(word in subject_lower for word in ["urgent", "asap", "important", "action required"]):
        priority = "high"
    elif any(word in subject_lower for word in ["newsletter", "digest", "weekly"]):
        priority = "low"
    
    # Basic sender type
    sender_type = "company"
    if "noreply" in sender_lower or "no-reply" in sender_lower:
        sender_type = "automated"
    elif "newsletter" in sender_lower:
        sender_type = "newsletter"
    
    return {
        "summary": (body[:1000] + ("..." if len(body) > 1000 else "")) if body else subject[:1000],
        "category": category,
        "priority": priority,
        "sender_type": sender_type,
        "action_required": "urgent" in subject_lower or "action" in subject_lower,
        "action_deadline": None
    }





def generate_dashboard_summary(summaries: list, filters=None) -> str:
    """
    Generate a contextual summary for the dashboard based on filters
    """
    if not is_gemini_configured():
        return "⚠️ AI Configuration Missing. Please set up your API key in Settings."
        
    if not summaries:
        return "No emails found matching the current filters."

    # Context description
    context = "Inbox"
    if filters:
        parts = []
        if filters.date_range: parts.append(f"Date: {filters.date_range}")
        if filters.priority: parts.append(f"Priority: {filters.priority}")
        if filters.category: parts.append(f"Category: {filters.category}")
        if parts: context = " | ".join(parts)

    # Prepare content
    # limit to 200 emails (Gemini 1.5/2.0/3.0 large context)
    limited_summaries = summaries[:200]
    
    email_texts = []
    for s in limited_summaries:
        sender = getattr(s, 'sender', 'Unknown')
        subject = getattr(s, 'subject', 'No Subject')
        content = getattr(s, 'summary', 'No content')
        priority = getattr(s, 'priority', 'medium')
        email_texts.append(f"- [{priority.upper()}] From: {sender} | Sub: {subject} | {content}")
        
    combined_text = "\n".join(email_texts)
    
    prompt = f"""
    You are an executive assistant. Write a short, high-level summary of the following emails.
    Context: {context}
    
    IMPORTANT: Provide the response in strict Markdown format. **Do NOT use any HTML tags.**
    
    Format:
    # 📝 Executive Summary
    (1-2 sentences overview)
    
    ## 🔥 Key Highlights
    - (Bullet points of most important items)
    
    ## 📊 Quick Stats
    - Total emails: {len(summaries)}
    
    Emails:
    {combined_text}
    """
    
    try:
        model = _get_gemini_model()
        if not model:
            return "Error: Could not initialize Gemini model."
            
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating dashboard report: {e}")
        return _fallback_report(summaries, context)


def _fallback_report(summaries, context):
    """Generate a local report when AI fails"""
    report = [f"# Summary: {context} (Offline Mode)\n"]
    report.append("> ⚠️ **Note:** AI unavailable (Quota Exceeded). Showing raw list.\n")
    
    # Simple list
    for s in summaries[:20]:
        subject = getattr(s, 'subject', 'No Subject')
        summary = getattr(s, 'summary', 'No content')
        report.append(f"- **{subject}**")
        report.append(f"  {summary}\n")
        
    if len(summaries) > 20:
        report.append(f"\n*...and {len(summaries) - 20} more.*")
        
    return "\n".join(report)



def batch_summarize_emails(emails: list) -> list:
    """Summarize and classify multiple emails"""
    results = []
    for email in emails:
        classification = summarize_and_classify_email(
            subject=email.get("subject", ""),
            sender=email.get("sender", ""),
            body=email.get("body", ""),
            has_attachments=email.get("has_attachments", False)
        )
        results.append({**email, **classification})
    return results
