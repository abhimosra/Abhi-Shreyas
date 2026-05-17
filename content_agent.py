import json
import anthropic
from config.settings import ANTHROPIC_API_KEY, BUSINESS_NAME
from instagram.publisher import check_publish_quota, publish_post

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""You are an Instagram content strategist for {BUSINESS_NAME}, a fine jewelry brand.

Create engaging Instagram post content that:
- Opens with a strong hook (the first line determines whether people tap "more")
- Uses a warm, aspirational tone — luxury but approachable
- Tells a story around the piece (the occasion, the feeling, who it's perfect for)
- Ends with a clear CTA directing followers to DM for pricing
- Selects 20-25 hashtags mixing high-volume tags (#jewelry, #goldnecklace) with niche tags \
  (#stackingrings, #bridaljewelry, #jewelrylover) — no spam-style hashtag dumps
- Uses line breaks for readability

Output ONLY valid JSON with these exact keys:
{{
  "caption": "...",
  "hashtags": ["...", "..."],
  "cta": "...",
  "full_post_text": "..."
}}

full_post_text should be: caption + two blank lines + hashtags joined by spaces + one blank line + cta
"""


def generate_post_content(topic: str, tone: str, product_focus: str | None = None) -> dict:
    user_prompt = f"Topic/theme: {topic}\nTone: {tone}"
    if product_focus:
        user_prompt += f"\nProduct focus: {product_focus}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if Claude wraps in ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def run_content_creation_cli():
    print(f"\n{'='*50}")
    print(f"  {BUSINESS_NAME} — Instagram Post Creator")
    print(f"{'='*50}\n")

    while True:
        topic = input("What's the theme or occasion for this post? (e.g. 'spring rings', 'Mother's Day gift')\n> ").strip()
        if not topic:
            print("Please enter a theme.")
            continue

        tone = input("\nWhat tone? (e.g. romantic, minimal, festive, bold)\n> ").strip() or "warm and aspirational"
        product_focus = input("\nSpecific product to highlight? (press Enter to skip)\n> ").strip() or None
        image_url = input("\nPaste the public HTTPS URL of your image:\n> ").strip()
        if not image_url.startswith("https://"):
            print("Image URL must start with https://")
            continue

        print("\nGenerating post content...")
        try:
            content = generate_post_content(topic, tone, product_focus)
        except Exception as e:
            print(f"Error generating content: {e}")
            continue

        print("\n" + "─"*50)
        print("PREVIEW:")
        print("─"*50)
        print(content["full_post_text"])
        print("─"*50)

        choice = input("\nOptions: [p]ublish, [r]egenerate, [q]uit\n> ").strip().lower()

        if choice == "p":
            try:
                quota = check_publish_quota()
                remaining = quota.get("quota_usage", {})
                print(f"Quota check: {remaining}")
            except Exception:
                print("Could not check quota — proceeding anyway.")

            print("Publishing to Instagram...")
            try:
                result = publish_post(image_url, content["full_post_text"])
                print(f"\nPublished! Media ID: {result['media_id']}")
                print("Your post is live on Instagram.")
            except Exception as e:
                print(f"Error publishing: {e}")

        elif choice == "r":
            print("Regenerating...\n")
            continue

        elif choice == "q":
            print("Exiting post creator.")
            break

        again = input("\nCreate another post? [y/n]\n> ").strip().lower()
        if again != "y":
            break
