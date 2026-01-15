"""
Configuration settings for the Email Summarizer Bot
"""
from pydantic import BaseModel
from typing import Optional
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")


class IMAPConfig(BaseModel):
    """IMAP server configuration"""
    imap_server: str  # e.g., "imap.gmail.com"
    imap_port: int = 993  # Default IMAP SSL port
    email: str
    password: str
    mailbox: str = "INBOX"
    use_ssl: bool = True


def save_config(config: IMAPConfig) -> None:
    """Save IMAP configuration to local file"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config.model_dump(), f, indent=2)


def load_config() -> Optional[IMAPConfig]:
    """Load IMAP configuration from local file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return IMAPConfig(**data)
    return None


def config_exists() -> bool:
    """Check if configuration file exists"""
    return os.path.exists(CONFIG_FILE)
