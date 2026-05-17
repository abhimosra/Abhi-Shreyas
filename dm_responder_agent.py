import json
import anthropic
from config.settings import ANTHROPIC_API_KEY, BUSINESS_NAME
from tools.catalog_tools import execute_tool
from data.conversation_memory import load_history, save_history
from data.lead_logger import log_lead

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""You are a friendly customer service assistant for {BUSINESS_NAME}, a jewelry brand on Instagram.

Your job is to answer questions that come in through DMs about products, pricing, sizes, shipping and policies.

Rules:
- Sound like a real person texting, not a brand. Casual, warm, short.
- Never use em-dashes (—). Use commas or short sentences instead.
- Always use the catalog tools to look up real prices. Never guess.
- Keep replies short. 3 to 5 sentences max. This is a DM not an email.
- End with a gentle nudge to order (e.g. "lmk if you want to grab one!", "happy to sort that out for you").
- Mention free shipping when the order qualifies (over $75 ships free).
- Never ask for personal info like address or email in DMs. Just confirm the item and say you'll send a payment link when they're ready.
- If someone asks about something not in the catalog, be honest and ask them to describe it more so you can help.
"""

CATALOG_TOOLS = [
    {
        "name": "search_products",
        "description": (
            "Search the jewelry product catalog for items matching a customer's inquiry. "
            "Use this when a customer asks about specific types of jewelry, materials, or product names. "
            "Returns product name, price, materials, available sizes/lengths, and in-stock status. "
            "Do NOT use this for shipping or policy questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms, e.g. 'pearl necklace', 'gold ring', 'stacking bracelet'"
                },
                "category": {
                    "type": "string",
                    "enum": ["rings", "necklaces", "earrings", "bracelets"],
                    "description": "Optional category to narrow results"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_product_by_sku",
        "description": (
            "Retrieve full details for a specific product by its SKU. "
            "Use when you already have a SKU from a previous search result."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Product SKU, e.g. 'NC-001'"}
            },
            "required": ["sku"]
        }
    },
    {
        "name": "get_shipping_info",
        "description": (
            "Returns shipping costs, carriers, and estimated delivery times. "
            "Use when a customer asks about shipping, delivery speed, or where you ship to."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination_type": {
                    "type": "string",
                    "enum": ["domestic_standard", "domestic_express", "international"],
                    "description": "Shipping type based on customer location and urgency"
                }
            },
            "required": ["destination_type"]
        }
    },
    {
        "name": "get_store_policies",
        "description": (
            "Returns return policy, custom order info, gift wrapping, and payment methods. "
            "Use when a customer asks about returns, exchanges, custom engravings, gift options, or how to pay."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_price_range",
        "description": (
            "Returns the min and max price for all products or a specific category. "
            "Use when a customer asks a general question like 'how much are your necklaces?' "
            "without specifying a particular item."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["rings", "necklaces", "earrings", "bracelets"],
                    "description": "Optional category filter"
                }
            },
            "required": []
        }
    }
]


def respond_to_dm(sender_igsid: str, message_text: str) -> str:
    """
    Runs the Claude agentic loop for an incoming DM.
    Loads prior conversation history, tracks which products were mentioned,
    logs the lead, and saves updated history before returning the reply.
    """
    history = load_history(sender_igsid)
    messages = history + [{"role": "user", "content": message_text}]
    products_mentioned = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            tools=CATALOG_TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            reply = "Thanks for reaching out! Let me get back to you shortly."
            for block in response.content:
                if hasattr(block, "text"):
                    reply = block.text
                    break

            messages.append({"role": "assistant", "content": reply})
            save_history(sender_igsid, messages)
            log_lead(sender_igsid, message_text, products_mentioned)
            return reply

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
                    # Track product names that came up during this conversation
                    if block.name in ("search_products", "get_product_by_sku"):
                        try:
                            parsed = json.loads(result)
                            if parsed.get("found"):
                                if "products" in parsed:
                                    products_mentioned += [p["name"] for p in parsed["products"]]
                                elif "product" in parsed:
                                    products_mentioned.append(parsed["product"]["name"])
                        except Exception:
                            pass

            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Thanks for your message! We'll get back to you shortly."
