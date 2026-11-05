import logging

import httpx

from . import config

log = logging.getLogger("slack")


def _esc(text: str) -> str:
    """Escape the three characters Slack treats specially in mrkdwn."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _label(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


def lead_message(lead: dict, fields: dict[str, str]) -> dict:
    name = fields.get("full_name") or fields.get("first_name") or fields.get("email") or "New lead"
    answers = "\n".join(f"*{_esc(_label(k))}:* {_esc(v)}" for k, v in fields.items()) or "_No answers_"
    meta = " · ".join(
        f"{label}: {_esc(lead[key])}"
        for label, key in (("Campaign", "campaign_name"), ("Ad", "ad_name"), ("Submitted", "created_time"), ("Lead ID", "id"))
        if lead.get(key)
    )
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"🆕 New lead: {name}"[:150], "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": answers[:3000]}},
    ]
    if meta:
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": meta[:3000]}]})
    # `text` is the fallback shown in notifications and previews.
    return {"text": f"New lead: {name}", "blocks": blocks}


async def post_lead(lead: dict, fields: dict[str, str]) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(config.SLACK_WEBHOOK_URL, json=lead_message(lead, fields))
    if resp.status_code != 200:
        raise RuntimeError(f"Slack returned {resp.status_code}: {resp.text}")
    log.info("Slack message posted for lead %s", lead.get("id"))
