"""
Email extractor module.
Attempts to extract email addresses from business websites.
This is a best-effort module — not all websites expose emails.
"""

import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

# Regex pattern for email addresses
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE,
)

# Common pages where contact info is found
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
    "/aboutus",
]

# Emails to exclude (generic/spam patterns)
EXCLUDED_PATTERNS = [
    "example.com",
    "domain.com",
    "email.com",
    "yourname@",
    "test@",
    "noreply@",
    "no-reply@",
    "sentry.io",
    "wixpress.com",
    "googleapis.com",
    ".png",
    ".jpg",
    ".gif",
    ".svg",
    ".css",
    ".js",
]


def _is_valid_email(email: str) -> bool:
    """Check if an email is likely a real contact email."""
    email_lower = email.lower()
    for pattern in EXCLUDED_PATTERNS:
        if pattern in email_lower:
            return False
    # Must have a reasonable length
    if len(email) < 6 or len(email) > 100:
        return False
    return True


def _extract_emails_from_html(html: str) -> set:
    """Extract all email addresses from HTML content."""
    emails = set()
    found = EMAIL_PATTERN.findall(html)
    for email in found:
        if _is_valid_email(email):
            emails.add(email.lower())
    return emails


def extract_email_from_website(website_url: str, timeout: int = 10) -> str:
    """
    Attempt to extract an email address from a business website.
    
    Checks the homepage and common contact pages.
    
    Args:
        website_url: The business website URL
        timeout: Request timeout in seconds
        
    Returns:
        First valid email found, or empty string
    """
    if not website_url:
        return ""

    # Ensure URL has a scheme
    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url

    all_emails = set()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    })

    # Pages to check
    urls_to_check = [website_url]
    for path in CONTACT_PATHS:
        urls_to_check.append(urljoin(website_url, path))

    for url in urls_to_check:
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                emails = _extract_emails_from_html(response.text)
                all_emails.update(emails)

                # Also check for mailto: links
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith("mailto:"):
                        email = href.replace("mailto:", "").split("?")[0].strip()
                        if _is_valid_email(email):
                            all_emails.add(email.lower())

                # If we found emails, no need to check more pages
                if all_emails:
                    break

        except requests.exceptions.RequestException:
            continue
        except Exception:
            continue

    session.close()

    if all_emails:
        # Return the first email (prefer info@, contact@, admin@ etc.)
        priority_prefixes = ["info@", "contact@", "admin@", "enquir", "hello@", "mail@"]
        for prefix in priority_prefixes:
            for email in all_emails:
                if email.startswith(prefix):
                    return email
        return sorted(all_emails)[0]

    return ""


def extract_emails_for_places(rows: list) -> list:
    """
    Attempt to extract emails for all places that have websites.
    Updates the rows in-place and returns them.
    
    Args:
        rows: List of processed place row dictionaries
        
    Returns:
        Updated rows with email field populated where possible
    """
    websites_count = sum(1 for r in rows if r.get("website"))
    if websites_count == 0:
        console.print("  ℹ️  No websites found, skipping email extraction", style="dim")
        return rows

    console.print(
        f"\n📧 Extracting emails from {websites_count} websites...",
        style="bold",
    )

    found_count = 0
    for i, row in enumerate(rows, 1):
        website = row.get("website", "")
        if not website:
            continue

        name = row.get("business_name", "Unknown")
        console.print(f"  🌐 [{i}/{websites_count}] {name}...", style="dim", end=" ")

        email = extract_email_from_website(website)
        if email:
            row["email"] = email
            found_count += 1
            console.print(f"[green]✓ {email}[/green]")
        else:
            console.print("[dim]no email found[/dim]")

    console.print(
        f"  ✅ Found emails for [bold green]{found_count}/{websites_count}[/bold green] businesses"
    )
    return rows
