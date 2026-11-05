import hashlib
import hmac
import logging

import httpx

from . import config

log = logging.getLogger("meta")


def signature_is_valid(body: bytes, header: str | None) -> bool:
    """Check Meta's X-Hub-Signature-256 header against the raw request body."""
    if not header or not header.startswith("sha256=") or not config.APP_SECRET:
        return False
    expected = hmac.new(config.APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


async def fetch_lead(leadgen_id: str) -> dict:
    """Fetch the submitted answers for a lead. The webhook itself only carries IDs."""
    full = "id,created_time,form_id,ad_id,ad_name,campaign_name,field_data,is_organic"
    basic = "id,created_time,form_id,field_data"
    async with httpx.AsyncClient(timeout=15) as client:
        for fields in (full, basic):
            resp = await client.get(
                f"{config.GRAPH_URL}/{leadgen_id}",
                params={"access_token": config.PAGE_ACCESS_TOKEN, "fields": fields},
            )
            if resp.is_success:
                return resp.json()
            if fields == full:
                # Ad/campaign names can need extra ads permissions; retry with just the answers.
                log.warning("Lead %s: full fetch failed (%s), retrying without ad details", leadgen_id, resp.text)
        raise RuntimeError(f"Graph API error {resp.status_code}: {resp.text}")


def flatten_fields(lead: dict) -> dict[str, str]:
    """Turn [{'name': 'email', 'values': ['a@b.c']}] into {'email': 'a@b.c'}."""
    return {f["name"]: ", ".join(f.get("values", [])) for f in lead.get("field_data", [])}
