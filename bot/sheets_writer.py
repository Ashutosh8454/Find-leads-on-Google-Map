"""
Google Sheets writer module.
Creates a separate tab/worksheet for each search query.
Writes business data using gspread.
"""

import re
import gspread
from google.oauth2.service_account import Credentials
from rich.console import Console

console = Console()

# Column headers for the Google Sheet
HEADERS = [
    "Sr. No.",
    "Search Query",
    "Business Name",
    "Category",
    "Business Status",
    "Full Address",
    "Phone Number",
    "Website",
    "Email",
    "Google Maps Link",
    "Rating",
    "Total Reviews",
    "Opening Hours",
    "About / Description",
    "Review 1 (Best)",
    "Review 2",
    "Review 3",
    "Review 4",
    "Review 5",
    "Place ID",
    "Date Scraped",
]

# Row keys matching the headers (same order)
ROW_KEYS = [
    "sr_no",
    "search_query",
    "business_name",
    "category",
    "status",
    "address",
    "phone",
    "website",
    "email",
    "google_maps_link",
    "rating",
    "total_reviews",
    "opening_hours",
    "about",
    "review_1",
    "review_2",
    "review_3",
    "review_4",
    "review_5",
    "place_id",
    "date_scraped",
]

# Google API scopes needed
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _sanitize_tab_name(query: str) -> str:
    """
    Create a valid Google Sheets tab name from a search query.
    Sheet tab names have a max length of 100 chars and can't contain certain characters.
    """
    # Remove characters not allowed in sheet names
    name = re.sub(r'[\\/*?\[\]:]', '', query)
    # Trim whitespace
    name = name.strip()
    # Truncate to 100 chars (Google Sheets limit)
    if len(name) > 100:
        name = name[:97] + "..."
    # Capitalize nicely
    name = name.title()
    return name if name else "Search Results"


class SheetsWriter:
    """Writes business data to a Google Sheet, one tab per query."""

    def __init__(self, service_account_file: str, sheet_id: str):
        """
        Initialize the Sheets writer.
        
        Args:
            service_account_file: Path to the service account JSON file
            sheet_id: Google Sheet ID (from the URL)
        """
        self.service_account_file = service_account_file
        self.sheet_id = sheet_id
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    def connect(self) -> bool:
        """
        Authenticate and connect to the Google Sheet.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            console.print("\n📊 Connecting to Google Sheet...", style="bold")

            creds = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=SCOPES,
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)

            console.print(
                f"  ✅ Connected to: [bold green]{self.spreadsheet.title}[/bold green]"
            )
            return True

        except FileNotFoundError:
            console.print(
                f"  ❌ Service account file not found: {self.service_account_file}",
                style="bold red",
            )
            console.print(
                "     Please follow setup_guide.md to create your credentials.",
                style="dim",
            )
            return False
        except gspread.exceptions.SpreadsheetNotFound:
            console.print(
                "  ❌ Google Sheet not found! Make sure you shared the sheet "
                "with the service account email.",
                style="bold red",
            )
            return False
        except Exception as e:
            console.print(f"  ❌ Connection error: {e}", style="bold red")
            return False

    def _get_or_create_worksheet(self, query: str) -> gspread.Worksheet:
        """
        Get an existing worksheet for this query, or create a new one.
        Each query gets its own tab in the spreadsheet.
        
        Args:
            query: The search query (used as the tab name)
            
        Returns:
            The worksheet for this query
        """
        tab_name = _sanitize_tab_name(query)

        # Check if a tab with this name already exists
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]

        if tab_name in existing_sheets:
            console.print(
                f"  📑 Using existing tab: [bold cyan]{tab_name}[/bold cyan]",
                style="dim",
            )
            return self.spreadsheet.worksheet(tab_name)

        # Handle duplicate names by appending a number
        base_name = tab_name
        counter = 2
        while tab_name in existing_sheets:
            tab_name = f"{base_name} ({counter})"
            counter += 1

        # Create a new worksheet/tab
        try:
            worksheet = self.spreadsheet.add_worksheet(
                title=tab_name,
                rows=100,
                cols=len(HEADERS),
            )
            console.print(
                f"  📑 Created new tab: [bold cyan]{tab_name}[/bold cyan]"
            )
            return worksheet
        except Exception as e:
            console.print(f"  ⚠️  Could not create tab: {e}", style="yellow")
            # Fallback to first sheet
            return self.spreadsheet.sheet1

    def _ensure_headers(self, worksheet: gspread.Worksheet):
        """Write headers to the first row if they don't exist."""
        try:
            first_row = worksheet.row_values(1)
            if not first_row or first_row[0] != HEADERS[0]:
                worksheet.update("A1", [HEADERS])
                console.print("  📝 Headers written to tab", style="dim")

                # Format header row (bold, background color)
                header_range = f"A1:{chr(64 + len(HEADERS))}1"
                worksheet.format(header_range, {
                    "textFormat": {"bold": True, "foregroundColorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}},
                    "backgroundColor": {
                        "red": 0.15,
                        "green": 0.35,
                        "blue": 0.6,
                    },
                    "horizontalAlignment": "CENTER",
                })
        except Exception as e:
            console.print(f"  ⚠️  Could not set headers: {e}", style="yellow")

    def _get_existing_place_ids(self, worksheet: gspread.Worksheet) -> set:
        """Get set of place IDs already in the sheet to avoid duplicates."""
        try:
            # Place ID is in column T (index 20)
            place_id_col = worksheet.col_values(20)  # Column T
            return set(pid for pid in place_id_col[1:] if pid)  # Skip header
        except Exception:
            return set()

    def _get_next_serial(self, worksheet: gspread.Worksheet) -> int:
        """Get the next serial number based on existing data."""
        try:
            all_values = worksheet.col_values(1)  # Column A (Sr. No.)
            numbers = []
            for val in all_values[1:]:  # Skip header
                try:
                    numbers.append(int(val))
                except (ValueError, TypeError):
                    pass
            return max(numbers) + 1 if numbers else 1
        except Exception:
            return 1

    def write_businesses(self, rows: list, query: str) -> int:
        """
        Write business data rows to a dedicated tab in the Google Sheet.
        Creates a new tab named after the query.
        Skips duplicates based on Place ID.
        
        Args:
            rows: List of processed row dictionaries
            query: The search query (used for tab name)
            
        Returns:
            Number of new rows written
        """
        if not self.spreadsheet:
            console.print("  ❌ Not connected to sheet!", style="bold red")
            return 0

        # Get or create a worksheet tab for this query
        worksheet = self._get_or_create_worksheet(query)
        self._ensure_headers(worksheet)

        # Check for existing entries
        existing_ids = self._get_existing_place_ids(worksheet)
        next_serial = self._get_next_serial(worksheet)

        # Filter out duplicates and prepare rows
        new_rows = []
        skipped = 0
        for row in rows:
            place_id = row.get("place_id", "")
            if place_id in existing_ids:
                skipped += 1
                continue

            # Update serial number
            row["sr_no"] = next_serial
            next_serial += 1

            # Convert dict to list in correct column order
            row_values = [str(row.get(key, "")) for key in ROW_KEYS]
            new_rows.append(row_values)

        if skipped > 0:
            console.print(
                f"  ⏭️  Skipped [yellow]{skipped}[/yellow] duplicate entries",
                style="dim",
            )

        if not new_rows:
            console.print("  ℹ️  No new entries to write", style="dim")
            return 0

        # Write all rows at once (batch update for speed)
        try:
            worksheet.append_rows(
                new_rows,
                value_input_option="USER_ENTERED",
            )
            console.print(
                f"  ✅ Written [bold green]{len(new_rows)}[/bold green] "
                f"new entries to tab [bold cyan]{worksheet.title}[/bold cyan]!"
            )
            return len(new_rows)

        except Exception as e:
            console.print(f"  ❌ Error writing to sheet: {e}", style="bold red")
            return 0

    def get_sheet_url(self) -> str:
        """Get the URL of the Google Sheet."""
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"
