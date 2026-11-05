import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .mailer import lead_confirmation, lead_notification, send_email
from .slack import post_lead

log = logging.getLogger("notify")

LEADS_FILE = Path(__file__).resolve().parent.parent / "leads.jsonl"


async def handle_new_lead(lead: dict, fields: dict[str, str]) -> None:
    """Called once per new lead: save it, email the team, optionally email the lead."""
    record = {"received_at": datetime.now(timezone.utc).isoformat(), "fields": fields, "lead": lead}
    with LEADS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    log.info("NEW LEAD %s: %s", lead.get("id"), fields)

    lead_email = fields.get("email", "").strip() or None

    if config.NOTIFY_EMAILS:
        try:
            subject, text, html = lead_notification(lead, fields)
            # Reply-To = the lead, so the team can hit "Reply" to contact them directly.
            await send_email(config.NOTIFY_EMAILS, subject, text, html, reply_to=lead_email)
        except Exception as exc:
            log.error("Failed to send team notification for lead %s: %s", lead.get("id"), exc)
    else:
        log.warning("NOTIFY_EMAILS is empty; no team notification sent")

    if config.SLACK_WEBHOOK_URL:
        try:
            await post_lead(lead, fields)
        except Exception as exc:
            log.error("Failed to post lead %s to Slack: %s", lead.get("id"), exc)

    if config.SEND_LEAD_CONFIRMATION and lead_email:
        try:
            subject, text, html = lead_confirmation(fields)
            await send_email([lead_email], subject, text, html)
        except Exception as exc:
            log.error("Failed to send confirmation to lead %s: %s", lead.get("id"), exc)
