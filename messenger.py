import requests
from config.settings import PAGE_ACCESS_TOKEN, INSTAGRAM_API_BASE


class InstagramMessagingError(Exception):
    pass


def send_dm_reply(recipient_igsid: str, text: str) -> dict:
    """
    Sends a DM reply to an Instagram user via the Messaging API.
    Must be called within 24 hours of the original incoming message.
    Returns the recipient_id and message_id on success.
    """
    url = f"{INSTAGRAM_API_BASE}/me/messages"
    payload = {
        "recipient": {"id": recipient_igsid},
        "message": {"text": text},
        "access_token": PAGE_ACCESS_TOKEN,
    }
    resp = requests.post(url, json=payload)
    if not resp.ok:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text
        raise InstagramMessagingError(f"Messaging API error {resp.status_code}: {detail}")
    return resp.json()
