import json
import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from . import config
from .meta import fetch_lead, flatten_fields, signature_is_valid
from .notify import handle_new_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("webhook")

app = FastAPI(title="AT360 Lead Webhook")


@app.get("/health")
def health():
    return {
        "ok": True,
        "verify_token_set": bool(config.VERIFY_TOKEN),
        "app_secret_set": bool(config.APP_SECRET),
        "page_token_set": bool(config.PAGE_ACCESS_TOKEN),
    }


@app.get("/webhooks/meta", response_class=PlainTextResponse)
def verify(
    mode: str = Query("", alias="hub.mode"),
    token: str = Query("", alias="hub.verify_token"),
    challenge: str = Query("", alias="hub.challenge"),
):
    """Meta calls this when you click 'Verify and save' in the Webhooks settings."""
    if mode == "subscribe" and config.VERIFY_TOKEN and token == config.VERIFY_TOKEN:
        log.info("Webhook verified by Meta")
        return challenge
    log.warning("Webhook verification failed (mode=%r)", mode)
    raise HTTPException(status_code=403, detail="Verification failed")


async def process_lead(leadgen_id: str, form_id: str | None) -> None:
    try:
        lead = await fetch_lead(leadgen_id)
    except Exception as exc:  # keep going; Meta won't resend because we already returned 200
        log.error("Could not fetch lead %s (form %s): %s", leadgen_id, form_id, exc)
        return
    await handle_new_lead(lead, flatten_fields(lead))


@app.post("/webhooks/meta")
async def receive(request: Request, background: BackgroundTasks):
    body = await request.body()
    if not signature_is_valid(body, request.headers.get("X-Hub-Signature-256")):
        log.warning("Rejected webhook with invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body or b"{}")
    log.info("Webhook received: %s", payload)

    if payload.get("object") == "page":
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "leadgen":
                    continue
                value = change.get("value", {})
                form_id = str(value.get("form_id", ""))
                if config.FORM_IDS and form_id not in config.FORM_IDS:
                    log.info("Ignoring lead from form %s (not in META_FORM_IDS)", form_id)
                    continue
                if leadgen_id := value.get("leadgen_id"):
                    # Reply to Meta immediately; fetch + notify after the response is sent.
                    background.add_task(process_lead, str(leadgen_id), value.get("form_id"))

    return {"received": True}
