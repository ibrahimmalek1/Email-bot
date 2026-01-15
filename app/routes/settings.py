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


@router.post("/reset", tags=["Admin"])
async def hard_reset():
    """
    Emergency Data Reset
    Deletes: summaries.json, google_token.json, google_credentials.json
    """
    import os
    
    deleted = []
    base_path = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_path, "data")
    
    files_to_delete = ["summaries.json", "google_token.json", "google_credentials.json", "config.json"]
    
    for filename in files_to_delete:
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted.append(filename)
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
                
    return {
        "success": True, 
        "message": "System reset successfully",
        "deleted_files": deleted
    }
