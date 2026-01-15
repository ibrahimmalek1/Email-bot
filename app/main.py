"""
Email Summarizer Utility Bot - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.emails import router as emails_router
from app.routes.auth import router as auth_router
from app.routes.settings import router as settings_router
from app.routes.reports import router as reports_router

app = FastAPI(
    title="Email Summarizer Bot",
    description="""
    AI-powered email summarization and smart filtering.
    
    ## Features
    - 🤖 **AI Summarization** (Gemini) - Smart one-line summaries
    - 📂 **Auto-Categorization** - Primary/Social/Promotions/Updates
    - 🔴 **Priority Detection** - High/Medium/Low
    - 🔍 **Smart Filters** - Filter by category, priority, sender type, etc.
    - **Google OAuth** - Sign in with Google
    - **IMAP Support** - Any email provider
    
    ## Quick Start
    1. Get Gemini API key: https://aistudio.google.com/apikey
    2. POST to `/settings/gemini` with your key
    3. Setup Google OAuth or IMAP
    4. Fetch emails with AI summaries!
    """,
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router)
app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(reports_router)


@app.get("/", tags=["Root"])
async def root():
    """API root - health check and info"""
    from app.services.gemini_service import is_gemini_configured
    
    return {
        "name": "Email Summarizer Bot",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "ai_enabled": is_gemini_configured(),
        "features": [
            "AI Summarization (Gemini)",
            "Smart Categorization",
            "Priority Detection",
            "Action Required Detection",
            "Smart Filters"
        ]
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
