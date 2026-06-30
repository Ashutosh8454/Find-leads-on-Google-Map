#!/usr/bin/env python3
"""
Google Maps Business Finder Bot
================================
Search Google Maps for businesses and export details to Google Sheets.

Usage:
    python main.py "hospital in chakan"
    python main.py "industries in pune" --max-results 40
    python main.py --no-email "hotel in chakan"
    python main.py  (interactive mode)

Author: FindingBots
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from bot.google_maps import GoogleMapsSearcher
from bot.data_processor import process_all_places
from bot.email_extractor import extract_emails_for_places
from bot.sheets_writer import SheetsWriter

console = Console()

# ASCII Art Banner
BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          🗺️  Google Maps Business Finder Bot  🗺️            ║
║                                                              ║
║   Search businesses on Google Maps → Export to Google Sheet   ║
╚══════════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Display the bot banner."""
    console.print(BANNER, style="bold cyan")


def print_results_table(rows: list):
    """Display a summary table of found businesses."""
    table = Table(
        title="📋 Found Businesses",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold magenta",
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Business Name", style="bold white", max_width=30)
    table.add_column("Category", style="cyan", max_width=15)
    table.add_column("Phone", style="green", max_width=18)
    table.add_column("Rating", justify="center", max_width=8)
    table.add_column("Website", style="blue", max_width=25)

    for row in rows:
        rating = row.get("rating", "")
        if rating:
            try:
                r = float(rating)
                if r >= 4.5:
                    rating_style = "bold green"
                elif r >= 3.5:
                    rating_style = "yellow"
                else:
                    rating_style = "red"
                rating_display = Text(f"⭐ {rating}", style=rating_style)
            except ValueError:
                rating_display = Text(rating)
        else:
            rating_display = Text("-", style="dim")

        website = row.get("website", "")
        if website:
            # Shorten URL for display
            website = website.replace("https://", "").replace("http://", "")
            if len(website) > 25:
                website = website[:22] + "..."

        table.add_row(
            str(row.get("sr_no", "")),
            row.get("business_name", ""),
            row.get("category", ""),
            row.get("phone", "") or "-",
            rating_display,
            website or "-",
        )

    console.print(table)


def validate_config():
    """Validate that all required configuration is present."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
    service_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

    errors = []

    if not api_key or api_key == "your_google_maps_api_key_here":
        errors.append(
            "GOOGLE_MAPS_API_KEY not set. "
            "Add your API key to the .env file."
        )

    if not sheet_id:
        errors.append(
            "GOOGLE_SHEET_ID not set. "
            "Add your Google Sheet ID to the .env file."
        )

    if not os.path.exists(service_file):
        errors.append(
            f"Service account file not found: {service_file}\n"
            "     Download it from Google Cloud Console and place it in this folder.\n"
            "     See setup_guide.md for instructions."
        )

    if errors:
        console.print("\n❌ Configuration errors:", style="bold red")
        for error in errors:
            console.print(f"  • {error}", style="red")
        console.print(
            "\n📖 Follow the setup guide: [bold]setup_guide.md[/bold]",
            style="yellow",
        )
        return False

    return True


def run_search(query: str, max_results: int, skip_email: bool):
    """
    Run a full search pipeline for the given query.
    
    Args:
        query: Search query (e.g., "hospital in chakan")
        max_results: Maximum number of results
        skip_email: If True, skip email extraction
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    service_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

    # Step 1: Search Google Maps
    searcher = GoogleMapsSearcher(api_key=api_key, max_results=max_results)
    detailed_places = searcher.search_and_get_details(query)

    if not detailed_places:
        console.print(
            "\n😔 No results found. Try a different query.",
            style="bold yellow",
        )
        return

    # Step 2: Process data
    console.print("\n⚙️  Processing data...", style="bold")
    rows = process_all_places(detailed_places, query)

    # Step 3: Extract emails (optional)
    if not skip_email:
        rows = extract_emails_for_places(rows)
    else:
        console.print("\n⏭️  Skipping email extraction (--no-email flag)", style="dim")

    # Step 4: Show preview table
    print_results_table(rows)

    # Step 5: Write to Google Sheet
    writer = SheetsWriter(
        service_account_file=service_file,
        sheet_id=sheet_id,
    )

    if writer.connect():
        written = writer.write_businesses(rows, query)
        if written > 0:
            sheet_url = writer.get_sheet_url()
            console.print(
                Panel(
                    f"✅ [bold green]{written} businesses[/bold green] added to your Google Sheet!\n\n"
                    f"📊 Open sheet: [link={sheet_url}]{sheet_url}[/link]",
                    title="🎉 Success!",
                    border_style="green",
                )
            )


def interactive_mode(max_results: int, skip_email: bool):
    """Run the bot in interactive mode — keeps asking for queries."""
    console.print(
        "\n💡 [bold]Interactive Mode[/bold] — Type your search queries below.",
        style="cyan",
    )
    console.print(
        "   Examples: 'hospital in chakan', 'industries in pune', 'hotel near me'\n"
        "   Type [bold]'quit'[/bold] or [bold]'exit'[/bold] to stop.\n",
        style="dim",
    )

    while True:
        try:
            query = console.input("[bold cyan]🔍 Search query: [/bold cyan]").strip()

            if not query:
                continue

            if query.lower() in ("quit", "exit", "q", "stop"):
                console.print("\n👋 Goodbye!", style="bold cyan")
                break

            run_search(query, max_results, skip_email)
            console.print("\n" + "─" * 60 + "\n")

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!", style="bold cyan")
            break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🗺️ Google Maps Business Finder Bot — "
                    "Search businesses and export to Google Sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "hospital in chakan"
  python main.py "industries in pune" --max-results 40
  python main.py --no-email "hotel in chakan"
  python main.py                          # Interactive mode
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Search query (e.g., 'hospital in chakan'). "
             "If not provided, runs in interactive mode.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum results per query (default: from .env, max 60)",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email extraction from websites (faster)",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env file (default: .env)",
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv(args.env)

    # Set max results
    max_results = args.max_results or int(os.getenv("MAX_RESULTS", "45"))

    print_banner()

    # Validate configuration
    if not validate_config():
        sys.exit(1)

    console.print(
        f"  📍 Max results per query: [bold]{max_results}[/bold]",
        style="dim",
    )

    if args.query:
        # Single query mode
        run_search(args.query, max_results, args.no_email)
    else:
        # Interactive mode
        interactive_mode(max_results, args.no_email)


if __name__ == "__main__":
    main()
