#!/usr/bin/env python3
"""
Batch Runner — Queries 57 to 100
=================================
Runs all 44 search queries sequentially using the existing FindingBots pipeline.
Does NOT modify any existing files.

Usage:
    python batch_run.py
    python batch_run.py --no-email         # Skip email extraction (faster)
    python batch_run.py --max-results 30   # Override max results
    python batch_run.py --start 65         # Resume from query #65
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
from rich.table import Table

# Load the existing bot modules (no changes to them)
from bot.google_maps import GoogleMapsSearcher
from bot.data_processor import process_all_places
from bot.email_extractor import extract_emails_for_places
from bot.sheets_writer import SheetsWriter

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# ALL 44 QUERIES  (numbers 57 – 100)
# ─────────────────────────────────────────────────────────────────────────────
QUERIES = [
    # --- PROFESSIONAL SERVICES ---
    (57, "CA and tax consultants in Pune"),
    (58, "law firms in Pune"),
    (59, "HR consultancy firms in Pune"),
    (60, "digital marketing agencies in Pune"),
    (61, "printing and packaging companies in Pune"),
    (62, "courier services in Pune"),
    (63, "travel agents in Pune"),
    (64, "insurance agents in Pune"),

    # --- HOSPITALITY & TRAVEL ---
    (65, "hotels in Shivajinagar Pune"),
    (66, "guest houses in Pune"),
    (67, "resorts near Pune"),
    (68, "homestays in Pune"),
    (69, "car rental services in Pune"),
    (70, "taxi and cab services in Pune"),
    (71, "tour operators in Pune"),
    (72, "banquet halls in Pune"),

    # --- AUTO & TRANSPORT ---
    (73, "automobile repair garages in Pune"),
    (74, "car dealerships in Pune"),
    (75, "two wheeler showrooms in Pune"),
    (76, "car wash and detailing in Pune"),
    (77, "driving schools in Pune"),
    (78, "tyre shops in Pune"),
    (79, "EV charging stations in Pune"),
    (80, "auto accessories shops in Pune"),

    # --- NICHE & EMERGING ---
    (81, "pet shops in Pune"),
    (82, "veterinary clinics in Pune"),
    (83, "pet grooming services in Pune"),
    (84, "plant nurseries in Pune"),
    (85, "organic food stores in Pune"),
    (86, "co-working spaces in Pune"),
    (87, "tattoo studios in Pune"),
    (88, "laundry and dry cleaning in Pune"),

    # --- ELECTRONICS & IT ---
    (89, "mobile phone repair shops in Pune"),
    (90, "laptop service centers in Pune"),
    (91, "CCTV installation services in Pune"),
    (92, "security system companies in Pune"),
    (93, "solar panel installers in Pune"),
    (94, "home automation companies in Pune"),
    (95, "software training institutes in Pune"),
    (96, "IT hardware suppliers in Pune"),

    # --- HOME SERVICES ---
    (97, "packers and movers in Pune"),
    (98, "pest control services in Pune"),
    (99, "home cleaning services in Pune"),
    (100, "water purifier dealers in Pune"),
]


def run_one_query(query: str, max_results: int, skip_email: bool,
                  api_key: str, sheet_id: str, service_file: str) -> dict:
    """
    Run the full pipeline for a single query.
    Returns a summary dict with success/fail info.
    """
    try:
        # Step 1 – Search Google Maps
        searcher = GoogleMapsSearcher(api_key=api_key, max_results=max_results)
        detailed_places = searcher.search_and_get_details(query)

        if not detailed_places:
            return {"query": query, "status": "no_results", "written": 0}

        # Step 2 – Process data
        console.print("  ⚙️  Processing data...", style="bold")
        rows = process_all_places(detailed_places, query)

        # Step 3 – Extract emails (optional)
        if not skip_email:
            rows = extract_emails_for_places(rows)
        else:
            console.print("  ⏭️  Skipping email extraction (--no-email flag)", style="dim")

        # Step 4 – Write to Google Sheet
        writer = SheetsWriter(service_account_file=service_file, sheet_id=sheet_id)
        if writer.connect():
            written = writer.write_businesses(rows, query)
            sheet_url = writer.get_sheet_url()
            console.print(
                Panel(
                    f"✅ [bold green]{written} businesses[/bold green] added!\n"
                    f"📊 [link={sheet_url}]{sheet_url}[/link]",
                    title=f"🎉 Done: {query}",
                    border_style="green",
                )
            )
            return {"query": query, "status": "ok", "written": written}
        else:
            return {"query": query, "status": "sheet_error", "written": 0}

    except KeyboardInterrupt:
        raise
    except Exception as e:
        console.print(f"  ❌ Error: {e}", style="bold red")
        return {"query": query, "status": "error", "written": 0, "error": str(e)}


def print_final_summary(results: list, elapsed: float):
    """Print a final summary table of all runs."""
    table = Table(
        title="📋 Batch Run Summary",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold magenta",
    )
    table.add_column("#",          style="dim",        width=4,  justify="right")
    table.add_column("Query",      style="white",      max_width=45)
    table.add_column("Status",     justify="center",   max_width=12)
    table.add_column("Written",    justify="center",   max_width=8)

    total_written = 0
    for r in results:
        status = r["status"]
        written = r.get("written", 0)
        total_written += written

        if status == "ok":
            status_cell = "[bold green]✅ OK[/bold green]"
        elif status == "no_results":
            status_cell = "[yellow]⚠ 0 results[/yellow]"
        elif status == "sheet_error":
            status_cell = "[red]❌ Sheet[/red]"
        else:
            status_cell = "[red]❌ Error[/red]"

        table.add_row(
            str(r.get("num", "")),
            r["query"],
            status_cell,
            str(written) if written else "-",
        )

    console.print(table)
    console.print(
        Panel(
            f"🏁 Finished [bold]{len(results)}[/bold] queries in "
            f"[bold]{elapsed/60:.1f} minutes[/bold]\n"
            f"📊 Total businesses written: [bold green]{total_written}[/bold green]",
            title="✅ Batch Complete",
            border_style="cyan",
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Batch runner for FindingBots — queries 57-100",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_run.py                      # Run all 44 queries
  python batch_run.py --no-email           # Skip email extraction (faster)
  python batch_run.py --max-results 30     # Limit results per query
  python batch_run.py --start 73           # Resume from query number 73
        """,
    )
    parser.add_argument("--max-results", type=int, default=None,
                        help="Max results per query (default: from .env)")
    parser.add_argument("--no-email", action="store_true",
                        help="Skip email extraction from websites (faster)")
    parser.add_argument("--start", type=int, default=57,
                        help="Resume from this query number (default: 57)")
    parser.add_argument("--env", default=".env",
                        help="Path to .env file (default: .env)")
    args = parser.parse_args()

    # Load environment (same .env the main bot uses)
    load_dotenv(args.env)

    api_key     = os.getenv("GOOGLE_MAPS_API_KEY", "")
    sheet_id    = os.getenv("GOOGLE_SHEET_ID", "")
    service_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    max_results = args.max_results or int(os.getenv("MAX_RESULTS", "45"))

    # Validate config
    errors = []
    if not api_key or api_key == "your_google_maps_api_key_here":
        errors.append("GOOGLE_MAPS_API_KEY not set in .env")
    if not sheet_id:
        errors.append("GOOGLE_SHEET_ID not set in .env")
    if not os.path.exists(service_file):
        errors.append(f"Service account file not found: {service_file}")
    if errors:
        console.print("\n❌ Configuration errors:", style="bold red")
        for e in errors:
            console.print(f"  • {e}", style="red")
        sys.exit(1)

    # Filter to queries starting from --start
    queries_to_run = [(num, q) for num, q in QUERIES if num >= args.start]

    console.print(
        Panel(
            f"🚀 Starting batch run of [bold]{len(queries_to_run)}[/bold] queries\n"
            f"   Starting from query #{args.start}\n"
            f"   Max results per query: [bold]{max_results}[/bold]\n"
            f"   Email extraction: [bold]{'OFF' if args.no_email else 'ON'}[/bold]",
            title="🗺️  FindingBots — Batch Runner",
            border_style="cyan",
        )
    )

    results = []
    batch_start = time.time()

    for idx, (num, query) in enumerate(queries_to_run, 1):
        console.print(
            f"\n{'═'*60}\n"
            f"  [{idx}/{len(queries_to_run)}] Query #{num}: [bold cyan]{query}[/bold cyan]\n"
            f"{'═'*60}",
            style="bold",
        )

        try:
            result = run_one_query(
                query=query,
                max_results=max_results,
                skip_email=args.no_email,
                api_key=api_key,
                sheet_id=sheet_id,
                service_file=service_file,
            )
            result["num"] = num
            results.append(result)
        except KeyboardInterrupt:
            console.print("\n\n⛔ Interrupted by user — printing partial summary.", style="bold yellow")
            break

        # Polite delay between queries to avoid rate limits
        if idx < len(queries_to_run):
            console.print("  ⏳ Waiting 3 seconds before next query...", style="dim")
            time.sleep(3)

    elapsed = time.time() - batch_start
    print_final_summary(results, elapsed)


if __name__ == "__main__":
    main()
