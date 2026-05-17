import hashlib
import hmac
import threading
import logging
from flask import Flask, request, jsonify
from config.settings import WEBHOOK_VERIFY_TOKEN, INSTAGRAM_APP_SECRET, INSTAGRAM_USER_ID
from agents.dm_responder_agent import respond_to_dm
from instagram.messenger import send_dm_reply, InstagramMessagingError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _validate_signature(req: request) -> bool:
    """Validates the X-Hub-Signature-256 header to confirm the request is from Meta."""
    signature_header = req.headers.get("X-Hub-Signature-256", "")
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        INSTAGRAM_APP_SECRET.encode(),
        req.get_data(),
        hashlib.sha256,
    ).hexdigest()
    received = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, received)


def _handle_dm_async(sender_igsid: str, message_text: str):
    """Runs in a background thread so the webhook can return 200 immediately."""
    try:
        reply = respond_to_dm(sender_igsid, message_text)
        send_dm_reply(sender_igsid, reply)
        log.info(f"Replied to {sender_igsid}: {reply[:80]}...")
    except InstagramMessagingError as e:
        log.error(f"Failed to send DM reply to {sender_igsid}: {e}")
    except Exception as e:
        log.error(f"Unexpected error handling DM from {sender_igsid}: {e}")


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta webhook verification handshake."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        log.info("Webhook verified successfully.")
        return challenge, 200
    log.warning("Webhook verification failed — token mismatch.")
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def handle_event():
    """Receives Instagram webhook events (DMs)."""
    if not _validate_signature(request):
        log.warning("Invalid webhook signature — rejecting request.")
        return "Unauthorized", 401

    body = request.get_json(silent=True) or {}

    if body.get("object") != "instagram":
        return jsonify({"status": "ignored"}), 200

    for entry in body.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message = event.get("message", {})
            message_text = message.get("text", "").strip()

            # Skip echoes (messages sent by the bot itself)
            if str(sender_id) == str(INSTAGRAM_USER_ID):
                continue

            # Skip non-text messages (stickers, reactions, etc.)
            if not message_text:
                continue

            log.info(f"DM from {sender_id}: {message_text[:80]}")
            thread = threading.Thread(
                target=_handle_dm_async,
                args=(sender_id, message_text),
                daemon=True,
            )
            thread.start()

    # Always return 200 quickly — Meta will retry if we don't
    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200


def run_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    log.info(f"Starting DM responder webhook on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
