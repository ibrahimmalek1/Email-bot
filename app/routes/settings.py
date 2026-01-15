"""
Settings routes for API configuration
"""
from fastapi import APIRouter, HTTPException

from app.models.email import GeminiConfigRequest, ConfigResponse
from app.services.gemini_service import save_gemini_api_key, is_gemini_configured

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.post("/gemini", response_model=ConfigResponse)
async def configure_gemini(config: GeminiConfigRequest):
    """
    Configure Gemini API key for AI summarization.
    
    Get your free API key from: https://aistudio.google.com/apikey
    
    Once configured, email summaries will use AI for:
    - Better one-line summaries
    - Auto-categorization (Primary/Social/Promotions/Updates)
    - Priority detection (High/Medium/Low)
    - Action required detection
    """
    success = save_gemini_api_key(config.api_key)
    
    if success:
        return ConfigResponse(
            success=True,
            message="Gemini API key saved. AI summarization is now enabled!",
            configured=True
        )
    raise HTTPException(status_code=500, detail="Failed to save API key")


@router.get("/gemini/status", response_model=ConfigResponse)
async def get_gemini_status():
    """Check if Gemini AI is configured"""
    configured = is_gemini_configured()
    return ConfigResponse(
        success=True,
        message="Gemini AI enabled" if configured else "Gemini not configured. POST API key to /settings/gemini",
        configured=configured
    )
