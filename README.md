# Email Summarizer Utility Bot

A FastAPI-based backend that fetches emails via IMAP, summarizes them using extractive summarization, and stores results locally.

## Features

- 📧 **IMAP Support** - Works with any email provider (Gmail, Outlook, Yahoo, etc.)
- ✂️ **Extractive Summarization** - Key sentences extracted without external AI
- 💾 **Local Storage** - Summaries stored in JSON for quick access
- 📅 **Date & Time** - All emails include original date/time information

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload
```

### 3. Open Swagger UI

Navigate to: http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/emails/config` | Configure IMAP settings |
| GET | `/emails/config/status` | Check if configured |
| POST | `/emails/fetch` | Fetch & summarize emails |
| GET | `/emails/summaries` | Get all summaries |
| GET | `/emails/summaries/{id}` | Get specific summary |
| DELETE | `/emails/summaries/{id}` | Delete a summary |
| DELETE | `/emails/summaries` | Clear all summaries |

## IMAP Configuration Examples

### Gmail
```json
{
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "email": "your.email@gmail.com",
  "password": "your-app-password",
  "mailbox": "INBOX",
  "use_ssl": true
}
```

> **Note**: For Gmail, you need to create an [App Password](https://support.google.com/accounts/answer/185833)

### Outlook/Hotmail
```json
{
  "imap_server": "imap-mail.outlook.com",
  "imap_port": 993,
  "email": "your.email@outlook.com",
  "password": "your-password",
  "mailbox": "INBOX",
  "use_ssl": true
}
```

## Project Structure

```
utility bot/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   ├── models/
│   │   └── email.py      # Pydantic models
│   ├── services/
│   │   ├── imap_service.py   # Email fetching
│   │   ├── summarizer.py     # Text summarization
│   │   └── storage.py        # Local storage
│   └── routes/
│       └── emails.py     # API endpoints
├── data/
│   ├── config.json       # IMAP config (auto-created)
│   └── summaries.json    # Stored summaries
├── requirements.txt
└── README.md
```
