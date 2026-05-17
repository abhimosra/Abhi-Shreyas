import json
from pathlib import Path

CONVERSATIONS_DIR = Path(__file__).parent / "conversations"
MAX_MESSAGES = 20  # keep last 20 messages per user to avoid hitting token limits


def _user_file(instagram_id: str) -> Path:
    CONVERSATIONS_DIR.mkdir(exist_ok=True)
    return CONVERSATIONS_DIR / f"{instagram_id}.json"


def load_history(instagram_id: str) -> list[dict]:
    """Returns the stored message history for a user, or an empty list if none exists."""
    path = _user_file(instagram_id)
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save_history(instagram_id: str, messages: list[dict]):
    """
    Saves the message history for a user.
    Trims to the last MAX_MESSAGES to prevent unbounded growth.
    Strips out tool_use/tool_result blocks — only keeps text turns for readability.
    """
    clean = []
    for msg in messages:
        if isinstance(msg["content"], str):
            clean.append(msg)
        elif isinstance(msg["content"], list):
            # Only keep messages that have at least one text block
            text_blocks = [b for b in msg["content"] if isinstance(b, dict) and b.get("type") == "text"]
            if text_blocks:
                clean.append({"role": msg["role"], "content": text_blocks[0]["text"]})
    trimmed = clean[-MAX_MESSAGES:]
    with open(_user_file(instagram_id), "w") as f:
        json.dump(trimmed, f, indent=2)


def clear_history(instagram_id: str):
    path = _user_file(instagram_id)
    if path.exists():
        path.unlink()
