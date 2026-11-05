"""One-time setup: get a Page access token and subscribe the Page to the app's leadgen webhook.

Usage (from the project root, with META_SYSTEM_USER_TOKEN and META_PAGE_ID in .env):
    python -m scripts.setup_page
"""
import sys

import httpx

from app import config


def main() -> None:
    if not (config.SYSTEM_USER_TOKEN and config.PAGE_ID):
        sys.exit("Set META_SYSTEM_USER_TOKEN and META_PAGE_ID in .env first.")

    with httpx.Client(timeout=15) as client:
        r = client.get(
            f"{config.GRAPH_URL}/{config.PAGE_ID}",
            params={"fields": "name,access_token", "access_token": config.SYSTEM_USER_TOKEN},
        )
        if r.is_error:
            sys.exit(f"Could not get Page token: {r.text}")
        page = r.json()
        page_token = page["access_token"]
        print(f"Page: {page.get('name')} ({config.PAGE_ID})")

        r = client.post(
            f"{config.GRAPH_URL}/{config.PAGE_ID}/subscribed_apps",
            params={"subscribed_fields": "leadgen", "access_token": page_token},
        )
        if r.is_error:
            sys.exit(f"Could not subscribe Page to app: {r.text}")
        print("Subscribed Page to leadgen webhooks:", r.json())

        r = client.get(f"{config.GRAPH_URL}/{config.PAGE_ID}/subscribed_apps", params={"access_token": page_token})
        print("Current subscriptions:", r.json())

    print("\nAdd this to .env:\nMETA_PAGE_ACCESS_TOKEN=" + page_token)


if __name__ == "__main__":
    main()
