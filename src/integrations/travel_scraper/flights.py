"""
flights.py
-----------
Responsible for searching flight offers via Amadeus Self-Service API.

Exposes:
  - FlightQuery (dataclass): a typed container for user input parameters.
  - search_flights(q: FlightQuery) -> list[dict]: returns raw Amadeus offers.

We intentionally return the raw JSON dicts from Amadeus so the calling code
(LangChain/Streamlit) can decide how to render, sort, or post-process.
"""

from __future__ import annotations  # allows list[dict] typing on python <3.9
from dataclasses import (
    dataclass,
)  # dataclass is a decorator to auto-generate __init__, __repr__, etc.
from typing import Optional, List, Any, Dict

from .amadeus_client import AmadeusClient  # our OAuth + GET helper (Step 1)

# ^ relative import from the same package (the leading dot means this package)


# ------------------------------
# 1) A typed container of inputs
# ------------------------------
@dataclass
class FlightQuery:
    """
    A plain data-holder for flight search parameters.
    Using a dataclass makes construction and validation easier and keeps code tidy
    """

    origin_iata: str
    dest_iata: str
    depart_date: str
    return_date: Optional[str] = None
    adults: int = 1
    currency: str = "USD"
    max_results: int = 20
    max_price: Optional[float] = None
    non_stop: Optional[bool] = None
    travel_class: Optional[str] = None


# -------------------------------------
# 2) The main function the app will use
# -------------------------------------
def search_flights(q: FlightQuery) -> List[Dict]:
    """
    Call Amadeus Flight Offers Search (v2) with parameters from FlightQuery
    and return a list of raw offer dictionaries.

    Args:
        q (FlightQuery): the user's search parameters.
    Returns:
        List[Dict]: a list of flight offers as dicts (raw amadeus JSON).
    """
    # Create an API client. This will:
    # - lazily fetch/refresh a bearer token (OAuth2 client-credentials)
    # - provide a .get() method with Authorization header
    cli = AmadeusClient()

    # Build the querystring parameters as a Python dict[str, Any].
    # Keys must match Amadeus parameter names
    params: Dict[str, object] = {
        "originLocationCode": q.origin_iata,
        "destinationLocationCode": q.dest_iata,
        "departureDate": q.depart_date,
        "adults": q.adults,
        "currencyCode": q.currency,
        "max": q.max_results,
    }

    # Only add optional params if the user provided them.
    if q.return_date:
        params["returnDate"] = q.return_date
    if q.non_stop is not None:
        # Amadeus expects "true"/"false" strings for nonStop in some clients.
        params["nonStop"] = str(q.non_stop).lower()  # bool -> "true"/"false"
    if q.travel_class:
        params["travelClass"] = q.travel_class  # e.g., "Economy"

    # Perform the authenticated GET request. The client:
    #  - ensures a valid token exists
    #  - sends Authorization: Bearer <token>
    #  - raises a helpful error if HTTP status >= 400
    response_json: Dict = cli.get("/v2/shopping/flight-offers", params)

    # The payload envelope typically has a "data" key holding a list of offers.
    offers: List[Dict] = response_json.get("data", [])

    # Optional client-side budget filter: if max_price is set, drop offers that exceed it.
    if q.max_price is not None:

        def within_budget(offer: Dict) -> bool:
            """
            Defensice extraction: some offers might have different shapes.
            We try to parse price.grandTotal as a float and compare.
            """
            try:
                total_str = offer["price"]["grandTotal"]  # Type: str, eng, "742.15"
                total_val = float(total_str)
                return total_val <= q.max_price
            except Exception:
                # If price missing/unexpected, we keep the offer rather than accidentally dropping it
                return True

    return offers
