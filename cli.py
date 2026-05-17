#!/usr/bin/env python3
import argparse
import sys
import os

# Ensure the project root is on sys.path so all imports resolve correctly
sys.path.insert(0, os.path.dirname(__file__))


def cmd_create_post(_args):
    from agents.content_agent import run_content_creation_cli
    run_content_creation_cli()


def cmd_start_dm_responder(args):
    from webhook.server import run_server
    run_server(port=args.port, debug=args.debug)


def cmd_test_catalog(_args):
    from tools.catalog_tools import (
        search_products, get_product_by_sku,
        get_shipping_info, get_store_policies, get_price_range
    )
    print("\n=== Catalog Tool Smoke Tests ===\n")

    print("1. search_products('pearl necklace'):")
    print(search_products("pearl necklace"))

    print("\n2. search_products('ring', category='rings'):")
    print(search_products("ring", category="rings"))

    print("\n3. get_product_by_sku('NC-001'):")
    print(get_product_by_sku("NC-001"))

    print("\n4. get_product_by_sku('FAKE-999'):")
    print(get_product_by_sku("FAKE-999"))

    print("\n5. get_shipping_info('domestic_standard'):")
    print(get_shipping_info("domestic_standard"))

    print("\n6. get_shipping_info('international'):")
    print(get_shipping_info("international"))

    print("\n7. get_store_policies():")
    print(get_store_policies())

    print("\n8. get_price_range(category='earrings'):")
    print(get_price_range(category="earrings"))

    print("\n9. get_price_range() — all products:")
    print(get_price_range())

    print("\n=== All tests passed ===\n")


def cmd_test_dm(args):
    """Quick test of the DM responder without needing a live webhook."""
    from agents.dm_responder_agent import respond_to_dm
    message = args.message or "Hi! How much is your pearl necklace and how long does shipping take?"
    print(f"\nTest DM: \"{message}\"\n")
    reply = respond_to_dm("test_user_123", message)
    print(f"Agent reply:\n{reply}\n")


def cmd_run_outreach(args):
    from agents.outreach_agent import run_outreach
    run_outreach(dry_run=args.dry_run, max_comments=args.max_comments)


def cmd_view_leads(_args):
    from data.lead_logger import get_all_leads
    leads = get_all_leads()
    if not leads:
        print("\nNo leads yet. They will appear here once customers DM the account.\n")
        return
    print(f"\n{'='*70}")
    print(f"  LEADS ({len(leads)} total)")
    print(f"{'='*70}")
    for i, lead in enumerate(reversed(leads), 1):
        print(f"\n#{i}  {lead['timestamp']}  |  IG: {lead['instagram_id']}")
        print(f"    Asked: {lead['message'][:120]}")
        print(f"    Interested in: {lead['products_mentioned']}")
        print(f"    Status: {lead['status']}")
    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Instagram Marketing Agent — Jewelry Business",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  create-post         Generate and publish an Instagram post (interactive CLI)
  start-dm-responder  Start the webhook server that auto-replies to DMs
  test-catalog        Smoke test all catalog lookup tools
  test-dm             Test the DM agent with a sample message (no webhook needed)
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("create-post", help="Generate and publish an Instagram post")

    dm_parser = subparsers.add_parser("start-dm-responder", help="Start the DM auto-responder webhook server")
    dm_parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    dm_parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")

    subparsers.add_parser("test-catalog", help="Smoke test all catalog lookup tools")

    test_dm_parser = subparsers.add_parser("test-dm", help="Test the DM agent with a sample message")
    test_dm_parser.add_argument("--message", type=str, help="Custom DM message to test with")

    outreach_parser = subparsers.add_parser("run-outreach", help="Search hashtags and comment on posts to drive DMs")
    outreach_parser.add_argument("--dry-run", action="store_true", help="Preview comments without actually posting them")
    outreach_parser.add_argument("--max-comments", type=int, default=10, help="Max comments to post per run (default: 10)")

    subparsers.add_parser("view-leads", help="View all DM leads captured so far")

    args = parser.parse_args()

    if args.command == "create-post":
        cmd_create_post(args)
    elif args.command == "start-dm-responder":
        cmd_start_dm_responder(args)
    elif args.command == "test-catalog":
        cmd_test_catalog(args)
    elif args.command == "test-dm":
        cmd_test_dm(args)
    elif args.command == "run-outreach":
        cmd_run_outreach(args)
    elif args.command == "view-leads":
        cmd_view_leads(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
