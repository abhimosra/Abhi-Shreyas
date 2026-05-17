import requests
from config.settings import INSTAGRAM_USER_ID, PAGE_ACCESS_TOKEN, GRAPH_API_BASE


class HashtagSearchError(Exception):
    pass


def get_hashtag_id(hashtag: str) -> str:
    """
    Resolves a hashtag string (e.g. 'jewelrylover') to its Instagram hashtag ID.
    Note: Instagram limits you to 30 unique hashtag searches per week per account.
    """
    hashtag = hashtag.lstrip("#").lower().replace(" ", "")
    resp = requests.get(
        f"{GRAPH_API_BASE}/ig-hashtag-search",
        params={
            "user_id": INSTAGRAM_USER_ID,
            "q": hashtag,
            "access_token": PAGE_ACCESS_TOKEN,
        }
    )
    if not resp.ok:
        raise HashtagSearchError(f"Failed to resolve hashtag #{hashtag}: {resp.text}")
    data = resp.json().get("data", [])
    if not data:
        raise HashtagSearchError(f"No hashtag ID found for #{hashtag}")
    return data[0]["id"]


def get_recent_posts(hashtag_id: str, limit: int = 20) -> list[dict]:
    """
    Returns recent public posts for a given hashtag ID.
    Each post includes id, caption, media_type, timestamp, like_count, comments_count.
    """
    resp = requests.get(
        f"{GRAPH_API_BASE}/{hashtag_id}/recent_media",
        params={
            "user_id": INSTAGRAM_USER_ID,
            "fields": "id,caption,media_type,timestamp,like_count,comments_count",
            "access_token": PAGE_ACCESS_TOKEN,
            "limit": limit,
        }
    )
    if not resp.ok:
        raise HashtagSearchError(f"Failed to fetch recent posts: {resp.text}")
    return resp.json().get("data", [])


def post_comment(media_id: str, comment_text: str) -> dict:
    """
    Posts a comment on a public Instagram post.
    Returns the comment ID on success.
    """
    resp = requests.post(
        f"{GRAPH_API_BASE}/{media_id}/comments",
        data={
            "message": comment_text,
            "access_token": PAGE_ACCESS_TOKEN,
        }
    )
    if not resp.ok:
        raise HashtagSearchError(f"Failed to post comment on {media_id}: {resp.text}")
    return resp.json()
