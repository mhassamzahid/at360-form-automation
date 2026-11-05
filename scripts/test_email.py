"""Send a sample 'new lead' email to NOTIFY_EMAILS to check SMTP settings.

Usage:  python -m scripts.test_email
"""
import asyncio
import logging

from app import config
from app.notify import handle_new_lead

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SAMPLE_LEAD = {"id": "TEST-0000", "form_id": "TEST-FORM", "created_time": "2026-11-05T19:00:00+0000",
               "campaign_name": "Test campaign"}
SAMPLE_FIELDS = {"full_name": "Test Lead", "email": config.SMTP_USERNAME, "phone_number": "+1 555 0100"}

if __name__ == "__main__":
    print(f"SMTP {config.SMTP_USERNAME} @ {config.SMTP_HOST}:{config.SMTP_PORT} -> {config.NOTIFY_EMAILS}")
    asyncio.run(handle_new_lead(SAMPLE_LEAD, SAMPLE_FIELDS))
