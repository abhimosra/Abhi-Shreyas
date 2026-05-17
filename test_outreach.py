"""
Simulates the outreach agent using sample Instagram posts.
Claude does the real scoring and comment writing -- no Instagram credentials needed.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.outreach_agent import _should_comment, _write_comment

SAMPLE_POSTS = [
    {
        "hashtag": "giftsforher",
        "caption": "my best friend's wedding is in 3 weeks and i still have no idea what to get her!! she loves anything dainty and gold, help!!",
        "likes": 84,
    },
    {
        "hashtag": "jewelrylover",
        "caption": "obsessed with layered necklaces rn, anyone know good places to shop? looking for something not too expensive but quality",
        "likes": 112,
    },
    {
        "hashtag": "bridetobe",
        "caption": "just said yes!!! now the real work begins lol -- dress, flowers, jewelry... where do i even start",
        "likes": 340,
    },
    {
        "hashtag": "stackingrings",
        "caption": "can't stop adding to my ring stack send help lol these are all from different places",
        "likes": 67,
    },
    {
        "hashtag": "giftsforher",
        "caption": "mother's day is coming up and my mom loves pearls, any recommendations for a nice gift under $100?",
        "likes": 55,
    },
    {
        "hashtag": "jewelryoftheday",
        "caption": "buy from our store!! discount code SAVE20 for 20% off all items this week only!!",
        "likes": 12,
    },
    {
        "hashtag": "goldnecklace",
        "caption": "wearing my favorite gold necklace today, feeling so elegant",
        "likes": 203,
    },
    {
        "hashtag": "bridetobe",
        "caption": "bridesmaids gift ideas?? i want to get all 5 of them something special and meaningful, budget is around $50-60 each",
        "likes": 91,
    },
]

print("\n" + "="*60)
print("  OUTREACH AGENT -- LIVE RUN (sample posts)")
print("="*60)

commented = 0
for post in SAMPLE_POSTS:
    print(f"\n[#{post['hashtag']}] {post['likes']} likes")
    print(f"Caption: \"{post['caption']}\"")

    should, reason = _should_comment(post["caption"], post["likes"])

    if not should:
        print(f"SKIP -- {reason}")
        continue

    comment = _write_comment(post["caption"])
    print(f"COMMENT --> {comment}")
    commented += 1

print(f"\n{'='*60}")
print(f"  Done. Commented on {commented}/{len(SAMPLE_POSTS)} posts.")
print(f"{'='*60}\n")
