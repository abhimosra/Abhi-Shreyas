import requests
from config.settings import INSTAGRAM_USER_ID, PAGE_ACCESS_TOKEN, GRAPH_API_BASE


class InstagramAPIError(Exception):
    pass


def _raise_for_error(response: requests.Response):
    if not response.ok:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except Exception:
            detail = response.text
        raise InstagramAPIError(f"Instagram API error {response.status_code}: {detail}")


def check_publish_quota() -> dict:
    """Returns the current content publishing quota usage (max 50 posts per 24h)."""
    url = f"{GRAPH_API_BASE}/{INSTAGRAM_USER_ID}/content_publishing_limit"
    resp = requests.get(url, params={
        "fields": "config,quota_usage",
        "access_token": PAGE_ACCESS_TOKEN,
    })
    _raise_for_error(resp)
    data = resp.json().get("data", [])
    return data[0] if data else {}


def create_image_container(image_url: str, caption: str) -> str:
    """
    Step 1 of 2: Creates a media container on Instagram.
    The image_url must be a publicly accessible HTTPS URL.
    Returns the container ID.
    """
    url = f"{GRAPH_API_BASE}/{INSTAGRAM_USER_ID}/media"
    resp = requests.post(url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": PAGE_ACCESS_TOKEN,
    })
    _raise_for_error(resp)
    return resp.json()["id"]


def publish_container(container_id: str) -> str:
    """
    Step 2 of 2: Publishes the media container to the Instagram feed.
    Returns the published media ID.
    """
    url = f"{GRAPH_API_BASE}/{INSTAGRAM_USER_ID}/media_publish"
    resp = requests.post(url, data={
        "creation_id": container_id,
        "access_token": PAGE_ACCESS_TOKEN,
    })
    _raise_for_error(resp)
    return resp.json()["id"]


def publish_post(image_url: str, caption: str) -> dict:
    """
    Full two-step publish flow. Returns container_id and media_id on success.
    Raises InstagramAPIError on failure.
    """
    container_id = create_image_container(image_url, caption)
    media_id = publish_container(container_id)
    return {"container_id": container_id, "media_id": media_id, "status": "published"}
