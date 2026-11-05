"""Post a sample lead to the Slack channel to check SLACK_WEBHOOK_URL.

Usage:  python -m scripts.test_slack
"""
import asyncio

from app import config
from app.slack import post_lead

SAMPLE_LEAD = {"id": "TEST-0000", "created_time": "2026-11-05T20:00:00+0000", "campaign_name": "Test campaign (ignore)"}
SAMPLE_FIELDS = {"full_name": "Test Lead (ignore)", "email": "test@example.com", "phone_number": "+1 555 0100"}

if __name__ == "__main__":
    if not config.SLACK_WEBHOOK_URL:
        raise SystemExit("SLACK_WEBHOOK_URL is not set in .env")
    asyncio.run(post_lead(SAMPLE_LEAD, SAMPLE_FIELDS))
    print("Posted test message to Slack.")
