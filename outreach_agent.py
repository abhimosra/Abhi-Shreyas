import json
import csv
import anthropic
from pathlib import Path
from datetime import datetime
from config.settings import ANTHROPIC_API_KEY, BUSINESS_NAME
from instagram.hashtag_searcher import get_hashtag_id, get_recent_posts, post_comment, HashtagSearchError

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Hashtags to search -- update these to match your client's niche
TARGET_HASHTAGS = [
    "jewelrylover",
    "jewelryoftheday",
    "bridetobe",
    "bridaljewelry",
    "stackingrings",
    "goldjewelry",
    "necklaceoftheday",
    "giftsforher",
    "jewelryaddict",
    "finejewelry",
]

COMMENTED_LOG = Path(__file__).parent.parent / "data" / "commented_posts.csv"

SCORING_PROMPT = f"""You are a lead generation assistant for {BUSINESS_NAME}, a jewelry brand.

You will be shown an Instagram post caption. Decide if it is worth leaving a comment to attract the person to our jewelry brand.

Good targets:
- Someone looking for a gift (birthday, anniversary, wedding, Mother's Day etc.)
- Someone posting about jewelry they love or want
- Someone asking for recommendations
- A bride or bridesmaid looking for accessories
- Someone celebrating a milestone

Skip these:
- Posts by other jewelry brands or sellers (competitors)
- Posts with no caption or irrelevant content
- Posts that are clearly advertisements
- Posts with very low engagement (under 5 likes)

Reply with JSON only:
{{
  "should_comment": true or false,
  "reason": "one short sentence explaining why"
}}"""

COMMENT_PROMPT = f"""You are writing an Instagram comment on behalf of {BUSINESS_NAME}, a jewelry brand.

Write a short, genuine comment that:
- Feels like a real person wrote it, not a bot
- Relates to what they posted about
- Naturally mentions that we have something they might love
- Ends with a soft invite to check our page or DM us
- Is 1 to 2 sentences max
- No hashtags in the comment
- No em-dashes
- Sounds warm and conversational

Post caption:
{{caption}}

Reply with just the comment text, nothing else."""


def _load_commented_ids() -> set:
    if not COMMENTED_LOG.exists():
        return set()
    with open(COMMENTED_LOG) as f:
        return {row["media_id"] for row in csv.DictReader(f)}


def _log_commented(media_id: str, hashtag: str, caption: str, comment: str):
    is_new = not COMMENTED_LOG.exists()
    with open(COMMENTED_LOG, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "media_id", "hashtag", "caption", "comment"])
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "media_id": media_id,
            "hashtag": hashtag,
            "caption": (caption or "")[:200],
            "comment": comment,
        })


def _should_comment(caption: str, like_count: int) -> tuple[bool, str]:
    if like_count < 5:
        return False, "too few likes"
    if not caption or len(caption.strip()) < 10:
        return False, "no caption"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": f"{SCORING_PROMPT}\n\nCaption:\n{caption[:500]}"
        }]
    )
    raw = response.content[0].text.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return result["should_comment"], result["reason"]
    except Exception:
        return False, f"could not parse scoring response: {raw[:80]}"


def _write_comment(caption: str) -> str:
    prompt = COMMENT_PROMPT.replace("{caption}", caption[:500])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def run_outreach(dry_run: bool = False, max_comments: int = 10):
    """
    Main outreach loop. Searches target hashtags, scores each post,
    and comments on the best ones to drive people to DM.

    dry_run=True shows what it WOULD do without actually posting comments.
    max_comments caps how many comments are posted per run.
    """
    already_commented = _load_commented_ids()
    comments_posted = 0

    print(f"\nStarting outreach run {'(DRY RUN)' if dry_run else ''}...")
    print(f"Searching {len(TARGET_HASHTAGS)} hashtags, will comment on up to {max_comments} posts.\n")

    for hashtag in TARGET_HASHTAGS:
        if comments_posted >= max_comments:
            break

        print(f"Searching #{hashtag}...")
        try:
            hashtag_id = get_hashtag_id(hashtag)
            posts = get_recent_posts(hashtag_id, limit=20)
        except HashtagSearchError as e:
            print(f"  Skipping #{hashtag}: {e}")
            continue

        for post in posts:
            if comments_posted >= max_comments:
                break

            media_id = post["id"]
            if media_id in already_commented:
                continue

            caption = post.get("caption", "")
            like_count = post.get("like_count", 0)

            should, reason = _should_comment(caption, like_count)

            if not should:
                print(f"  Skipping post {media_id}: {reason}")
                continue

            comment = _write_comment(caption)
            print(f"\n  Post {media_id} (#{hashtag}, {like_count} likes)")
            print(f"  Caption: {caption[:80]}...")
            print(f"  Comment: {comment}")

            if not dry_run:
                try:
                    post_comment(media_id, comment)
                    _log_commented(media_id, hashtag, caption, comment)
                    already_commented.add(media_id)
                    comments_posted += 1
                    print(f"  Posted comment.")
                except HashtagSearchError as e:
                    print(f"  Failed to post comment: {e}")
            else:
                _log_commented(media_id, hashtag, caption, comment)
                already_commented.add(media_id)
                comments_posted += 1
                print(f"  [DRY RUN] Would have posted this comment.")

    print(f"\nDone. {'Would have commented' if dry_run else 'Commented'} on {comments_posted} posts.")
