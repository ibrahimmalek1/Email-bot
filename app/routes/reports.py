from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services import storage
from app.services import gemini_service

router = APIRouter(prefix="/reports", tags=["Reports"])

from app.models.email import FilterEmailsRequest

@router.post("/summary")
async def generate_summary_report(filters: FilterEmailsRequest):
    """
    Generate a summary report based on applied filters
    """
    try:
        # 1. Fetch summaries based on filters
        summaries = storage.get_filtered_summaries(
            category=filters.category,
            priority=filters.priority,
            sender_type=filters.sender_type,
            action_required=filters.action_required,
            has_attachments=filters.has_attachments,
            date_range=filters.date_range,
            search=filters.search
        )
        
        # 2. Generate report using Gemini
        report_text = gemini_service.generate_dashboard_summary(summaries, filters)
        
        return {
            "email_count": len(summaries),
            "report": report_text
        }
    except Exception as e:
        print(f"Error generating report: {e}")
        # Return a friendly error instead of 500 so UI can handle it gracefully
        return {
            "email_count": 0,
            "report": f"Could not generate report: {str(e)}"
        }
