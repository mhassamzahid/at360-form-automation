import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return default


APP_ID = _env("META_APP_ID", "META_APP_id")
APP_SECRET = _env("META_APP_SECRET")
VERIFY_TOKEN = _env("META_VERIFY_TOKEN")
PAGE_ID = _env("META_PAGE_ID")
PAGE_ACCESS_TOKEN = _env("META_PAGE_ACCESS_TOKEN")
SYSTEM_USER_TOKEN = _env("META_SYSTEM_USER_TOKEN")
# Comma-separated lead form IDs to act on. Empty = all forms on the Page.
FORM_IDS = {f.strip() for f in _env("META_FORM_IDS").split(",") if f.strip()}
GRAPH_VERSION = _env("META_GRAPH_VERSION", default="v27.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Email (SMTP). Defaults are for Namecheap PrivateEmail.
SMTP_HOST = _env("SMTP_HOST", default="mail.privateemail.com")
SMTP_PORT = int(_env("SMTP_PORT", default="465"))
SMTP_USERNAME = _env("SMTP_USERNAME")  # full email address
SMTP_PASSWORD = _env("SMTP_PASSWORD")  # app password
EMAIL_FROM_NAME = _env("EMAIL_FROM_NAME", default="AheadTech360")
# Comma-separated addresses that get the "new lead" email
NOTIFY_EMAILS = [e.strip() for e in _env("NOTIFY_EMAILS", "TO_EMAILS").split(",") if e.strip()]
# Also email the person who filled the form?
SEND_LEAD_CONFIRMATION = _env("SEND_LEAD_CONFIRMATION", default="false").lower() in ("1", "true", "yes")
LEAD_CONFIRMATION_SUBJECT = _env("LEAD_CONFIRMATION_SUBJECT", default="Thanks, we've received your details")
