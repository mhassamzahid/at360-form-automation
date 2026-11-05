import asyncio
import logging
import smtplib
import ssl

import certifi
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from html import escape

from . import config

log = logging.getLogger("mailer")


def _send_sync(msg: EmailMessage) -> None:
    context = ssl.create_default_context(cafile=certifi.where())
    if config.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=context, timeout=30) as s:
            s.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            s.send_message(msg)
    else:  # 587 / STARTTLS
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as s:
            s.starttls(context=context)
            s.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            s.send_message(msg)


async def send_email(to: list[str], subject: str, text: str, html: str, reply_to: str | None = None) -> None:
    if not (config.SMTP_HOST and config.SMTP_USERNAME and config.SMTP_PASSWORD):
        raise RuntimeError("SMTP is not configured (SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD)")
    msg = EmailMessage()
    msg["From"] = formataddr((config.EMAIL_FROM_NAME, config.SMTP_USERNAME))
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=config.SMTP_USERNAME.split("@")[-1])
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    await asyncio.to_thread(_send_sync, msg)
    log.info("Email sent to %s: %s", to, subject)


def _label(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


def lead_notification(lead: dict, fields: dict[str, str]) -> tuple[str, str, str]:
    """Build (subject, text, html) for the internal 'new lead' email."""
    name = fields.get("full_name") or fields.get("first_name") or fields.get("email") or "New lead"
    subject = f"New lead: {name}"

    meta = {
        "Submitted": lead.get("created_time", ""),
        "Form ID": lead.get("form_id", ""),
        "Campaign": lead.get("campaign_name", ""),
        "Ad": lead.get("ad_name", ""),
        "Lead ID": lead.get("id", ""),
    }
    meta = {k: v for k, v in meta.items() if v}

    text = "\n".join(
        ["New lead from the Meta form:", ""]
        + [f"{_label(k)}: {v}" for k, v in fields.items()]
        + [""]
        + [f"{k}: {v}" for k, v in meta.items()]
    )

    def rows(items, muted=False):
        color = "#6b7280" if muted else "#111827"
        return "".join(
            f'<tr><td style="padding:6px 12px 6px 0;color:#6b7280;vertical-align:top;white-space:nowrap">{escape(k)}</td>'
            f'<td style="padding:6px 0;color:{color}">{escape(str(v))}</td></tr>'
            for k, v in items
        )

    html = f"""<div style="font-family:Arial,sans-serif;font-size:14px;max-width:560px">
<h2 style="margin:0 0 12px;font-size:18px">New lead: {escape(name)}</h2>
<table style="border-collapse:collapse">{rows((_label(k), v) for k, v in fields.items())}</table>
<hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0">
<table style="border-collapse:collapse;font-size:12px">{rows(meta.items(), muted=True)}</table>
</div>"""
    return subject, text, html


def lead_confirmation(fields: dict[str, str]) -> tuple[str, str, str]:
    """Build (subject, text, html) for the email sent to the person who filled the form."""
    first = (fields.get("first_name") or fields.get("full_name", "").split(" ")[0] or "there").strip()
    subject = config.LEAD_CONFIRMATION_SUBJECT
    text = (
        f"Hi {first},\n\n"
        f"Thanks for your interest in {config.EMAIL_FROM_NAME}. We've received your details "
        "and someone from our team will be in touch shortly.\n\n"
        f"Best regards,\n{config.EMAIL_FROM_NAME}"
    )
    html = f"""<div style="font-family:Arial,sans-serif;font-size:14px;max-width:560px;color:#111827">
<p>Hi {escape(first)},</p>
<p>Thanks for your interest in {escape(config.EMAIL_FROM_NAME)}. We've received your details
and someone from our team will be in touch shortly.</p>
<p>Best regards,<br>{escape(config.EMAIL_FROM_NAME)}</p>
</div>"""
    return subject, text, html
