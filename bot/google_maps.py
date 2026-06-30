"""
Google Maps Places API integration module.
Uses the classic Google Places API (already enabled, no billing required).
Provides 100% reliable business data directly from Google.

Pagination strategy:
  The old Places Text Search API's next_page_token requires billing to be
  enabled. Without billing, page 2+ always returns INVALID_REQUEST.
  Workaround: run up to 8 location-biased sub-searches around Pune and
  deduplicate results by place_id. This can yield 40-140 unique places
  without touching pagination at all.
"""

import requests
import time
from rich.console import Console

console = Console()


class GoogleMapsSearcher:
    """Search businesses on Google Maps using the classic Places API."""

    TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_URL     = "https://maps.googleapis.com/maps/api/place/details/json"

    # Fields for Place Details (basic + contact + atmosphere)
    DETAIL_FIELDS = (
        "name,formatted_address,formatted_phone_number,international_phone_number,"
        "website,url,rating,user_ratings_total,types,business_status,"
        "opening_hours,editorial_summary,reviews,place_id,geometry"
    )

    # Location offsets around Pune to widen coverage.
    # Each tuple is (lat_offset, lng_offset) from Pune centre (18.5204, 73.8567).
    _PUNE_OFFSETS = [
        ( 0.00,  0.00),   # city centre
        ( 0.09,  0.00),   # north (~10 km)
        (-0.09,  0.00),   # south
        ( 0.00,  0.09),   # east
        ( 0.00, -0.09),   # west
        ( 0.07,  0.07),   # NE
        (-0.07,  0.07),   # SE
    ]

    def __init__(self, api_key: str, max_results: int = 60):
        self.api_key     = api_key
        self.max_results = min(max_results, 140)   # 7 offsets × 20 results
        self.session     = requests.Session()

    # ------------------------------------------------------------------ #
    #  Internal: fetch one page (no pagination)                           #
    # ------------------------------------------------------------------ #
    def _fetch_one_page(self, query: str,
                        location: str = None,
                        radius: int = 10000) -> list:
        """
        Fetch a single page (≤ 20 results) from Text Search API.
        Returns list of place dicts, or [] on any error / non-OK status.
        """
        params = {
            "query": query,
            "key":   self.api_key,
        }
        if location:
            params["location"] = location
            params["radius"]   = radius

        try:
            resp = self.session.get(self.TEXT_SEARCH_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            console.print(f"  ❌ Network error: {e}", style="bold red")
            return []

        status = data.get("status", "")
        if status == "OK":
            return data.get("results", [])
        elif status == "ZERO_RESULTS":
            return []
        elif status == "REQUEST_DENIED":
            console.print(
                f"  ❌ API key error: {data.get('error_message', 'denied')}",
                style="bold red",
            )
            return []
        else:
            # INVALID_REQUEST / OVER_QUERY_LIMIT — silently skip
            return []

    # ------------------------------------------------------------------ #
    #  Public: search_places                                              #
    # ------------------------------------------------------------------ #
    def search_places(self, query: str) -> list:
        """
        Search for places using the Text Search API.

        Uses a multi-pass location-bias strategy to collect more than 20
        unique results without needing next_page_token (which requires billing).

        Returns a deduplicated list of place dicts, trimmed to max_results.
        """
        seen_ids:   set  = set()
        all_places: list = []

        BASE_LAT, BASE_LNG = 18.5204, 73.8567   # Pune city centre

        # Pass 1: plain (no location bias)
        passes = [("no bias", None)] + [
            (f"{BASE_LAT + dlat:.4f},{BASE_LNG + dlng:.4f}",
             f"{BASE_LAT + dlat:.4f},{BASE_LNG + dlng:.4f}")
            for dlat, dlng in self._PUNE_OFFSETS
        ]

        for pass_num, (label, location) in enumerate(passes, start=1):
            if len(all_places) >= self.max_results:
                break

            console.print(
                f"  📄 Pass {pass_num}/{len(passes)} [{label}]...",
                style="dim",
            )

            results = self._fetch_one_page(query, location=location)
            added = 0
            for p in results:
                pid = p.get("place_id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_places.append(p)
                    added += 1

            console.print(
                f"      → +{added} new  |  {len(all_places)} unique total",
                style="dim",
            )

            if pass_num < len(passes):
                time.sleep(0.4)   # polite delay between sub-searches

        return all_places[:self.max_results]

    # ------------------------------------------------------------------ #
    #  Public: get_place_details                                          #
    # ------------------------------------------------------------------ #
    def get_place_details(self, place_id: str) -> dict:
        """
        Get detailed information for a specific place.

        Args:
            place_id: The place_id from search results

        Returns:
            Dictionary with full place details including reviews
        """
        params = {
            "place_id":     place_id,
            "fields":       self.DETAIL_FIELDS,
            "key":          self.api_key,
            "reviews_sort": "most_relevant",
        }

        try:
            response = self.session.get(
                self.DETAILS_URL,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status", "")
            if status == "OK":
                return data.get("result", {})
            else:
                console.print(
                    f"  ⚠️  Details error for {place_id}: {status}",
                    style="yellow",
                )
                return {}

        except requests.exceptions.RequestException as e:
            console.print(
                f"  ⚠️  Network error fetching {place_id}: {e}",
                style="yellow",
            )
            return {}

    # ------------------------------------------------------------------ #
    #  Public: search_and_get_details                                     #
    # ------------------------------------------------------------------ #
    def search_and_get_details(self, query: str) -> list:
        """
        Full pipeline: search for places and get detailed info for each.

        Args:
            query: Search query like "hospital in chakan"

        Returns:
            List of dictionaries with full place details
        """
        console.print(f"\n🔍 Searching: [bold cyan]{query}[/bold cyan]")

        # Step 1: Multi-pass text search
        places = self.search_places(query)
        console.print(f"  ✅ Found [bold green]{len(places)}[/bold green] places")

        if not places:
            return []

        # Step 2: Get details for each place
        detailed_places = []
        for i, place in enumerate(places, 1):
            place_id   = place.get("place_id", "")
            place_name = place.get("name", "Unknown")
            console.print(
                f"  📋 [{i}/{len(places)}] Getting details: {place_name}",
                style="dim",
            )

            details = self.get_place_details(place_id)
            if details:
                detailed_places.append(details)

            # Rate limiting: small delay between detail requests
            if i < len(places):
                time.sleep(0.3)

        console.print(
            f"  ✅ Got details for [bold green]{len(detailed_places)}[/bold green] places"
        )
        return detailed_places
