"""
Data processor module.
Cleans, formats, and structures raw API data for Google Sheets output.
Works with the classic Google Places API response format.
"""

from datetime import datetime


def extract_reviews(details: dict, max_reviews: int = 5) -> list:
    """
    Extract and format the top reviews from place details.
    
    Args:
        details: Place details dictionary from the API
        max_reviews: Number of reviews to extract (default 5)
        
    Returns:
        List of formatted review strings
    """
    reviews = details.get("reviews", [])
    formatted = []

    # Sort by rating (highest first) to get the best reviews
    sorted_reviews = sorted(
        reviews,
        key=lambda r: r.get("rating", 0),
        reverse=True,
    )

    for review in sorted_reviews[:max_reviews]:
        author = review.get("author_name", "Anonymous")
        rating = review.get("rating", "N/A")
        text = review.get("text", "No review text")

        # Clean up the review text (remove excessive newlines)
        text = " ".join(text.split())

        # Truncate very long reviews to keep sheet readable
        if len(text) > 500:
            text = text[:497] + "..."

        formatted.append(f"⭐{rating}/5 by {author}: {text}")

    # Pad with empty strings if fewer reviews than max
    while len(formatted) < max_reviews:
        formatted.append("")

    return formatted


def extract_opening_hours(details: dict) -> str:
    """
    Extract and format opening hours.
    
    Args:
        details: Place details dictionary
        
    Returns:
        Formatted opening hours string
    """
    hours = details.get("opening_hours", {})
    descriptions = hours.get("weekday_text", [])

    if descriptions:
        return " | ".join(descriptions)

    return ""


def format_types(types: list) -> str:
    """Format place types into a readable category string."""
    if not types:
        return ""
    # Take the first type and format it nicely
    primary = types[0] if types else ""
    return primary.replace("_", " ").title()


def process_place_details(details: dict, query: str, serial_no: int) -> dict:
    """
    Process raw API response into a clean row for the Google Sheet.
    
    Args:
        details: Raw place details from the classic Places API
        query: The original search query
        serial_no: Serial number for this row
        
    Returns:
        Dictionary with all columns for the Google Sheet
    """
    # Extract basic fields
    display_name = details.get("name", "")
    address = details.get("formatted_address", "")

    # Phone numbers
    phone = details.get("formatted_phone_number", "")
    intl_phone = details.get("international_phone_number", "")
    phone_display = phone if phone else intl_phone

    # Website
    website = details.get("website", "")

    # Google Maps link (the 'url' field is the direct Google Maps URL)
    google_maps_link = details.get("url", "")

    # Rating and reviews count
    rating = details.get("rating", "")
    total_reviews = details.get("user_ratings_total", "")

    # Category/type
    types = details.get("types", [])
    primary_type = format_types(types)

    # About/description
    about = details.get("editorial_summary", {}).get("overview", "") if isinstance(
        details.get("editorial_summary"), dict
    ) else ""

    # Opening hours
    opening_hours = extract_opening_hours(details)

    # Business status
    status = details.get("business_status", "")
    if status:
        status = status.replace("_", " ").title()

    # Reviews (top 5)
    reviews = extract_reviews(details, max_reviews=5)

    # Place ID for reference
    place_id = details.get("place_id", "")

    # Build the row
    return {
        "sr_no": serial_no,
        "search_query": query,
        "business_name": display_name,
        "category": primary_type,
        "status": status,
        "address": address,
        "phone": phone_display,
        "website": website,
        "email": "",  # Will be filled by email extractor
        "google_maps_link": google_maps_link,
        "rating": str(rating) if rating else "",
        "total_reviews": str(total_reviews) if total_reviews else "",
        "opening_hours": opening_hours,
        "about": about,
        "review_1": reviews[0],
        "review_2": reviews[1],
        "review_3": reviews[2],
        "review_4": reviews[3],
        "review_5": reviews[4],
        "place_id": place_id,
        "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def process_all_places(detailed_places: list, query: str, start_serial: int = 1) -> list:
    """
    Process a list of place details into sheet-ready rows.
    
    Args:
        detailed_places: List of raw place details
        query: The search query used
        start_serial: Starting serial number
        
    Returns:
        List of processed row dictionaries
    """
    rows = []
    for i, details in enumerate(detailed_places):
        row = process_place_details(details, query, start_serial + i)
        rows.append(row)
    return rows
