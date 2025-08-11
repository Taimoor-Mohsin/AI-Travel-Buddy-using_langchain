"""
hotels.py
---------
Hotel search flow (TEST env friendly) for Amadeus v3:

STEP 1: Use Hotel List API to fetch hotels for a city (returns hotelId, name, address, geo...)
        GET /v1/reference-data/locations/hotels/by-city?cityCode=ROM

STEP 2: Use Hotel Search v3 to fetch OFFERS for a set of hotelIds
        GET /v3/shopping/hotel-offers?hotelIds=ID1,ID2,...&adults=1&checkInDate=YYYY-MM-DD&checkOutDate=YYYY-MM-DD&currency=USD

Why do we do STEP 1 first?
- In v3, /shopping/hotel-offers *requires* hotelIds and removed cityCode.
  To search by city or coordinates, Amadeus now directs you to the Hotel List API first.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from .amadeus_client import AmadeusClient  # your OAuth+HTTP helper


@dataclass
class HotelQuery:
    """
    Typed container for hotel search inputs.

    Data types (Python typing):
      - city_code:   str            (IATA city code e.g. "ROM")
      - check_in:    str            ("YYYY-MM-DD")
      - check_out:   str            ("YYYY-MM-DD")
      - adults:      int            (1..9)
      - currency:    str            (ISO 4217 e.g. "USD")
      - max_hotels:  int            (# of hotelIds to include in v3 search)
    """

    city_code: str
    check_in: str
    check_out: str
    adults: int = 1
    currency: str = "USD"
    max_hotels: int = 25


def list_hotels_by_city(city_code: str) -> List[Dict]:
    """
    STEP 1: Call Hotel List API by city to get hotel “static” records.

    Returns:
      list[dict] where each dict typically contains:
        - hotelId (str, 8 chars like "RTPAR001")
        - name, address, latitude/longitude, etc. (varies)
    """
    cli = AmadeusClient()
    # Minimal required param is cityCode. (We avoid extra filters to keep it simple in TEST.)
    payload: Dict = cli.get(
        "/v1/reference-data/locations/hotels/by-city", {"cityCode": city_code}
    )
    return payload.get("data", [])


def search_hotel_offers_by_ids(
    hotel_ids: List[str],
    check_in: str,
    check_out: str,
    adults: int = 1,
    currency: str = "USD",
    best_rate_only: bool = True,
) -> List[Dict]:
    """
    STEP 2: Call Hotel Search v3 with hotelIds to retrieve offers.

    Required query params in v3:
      - hotelIds (comma-separated)
      - adults
      - checkInDate, checkOutDate
    """
    if not hotel_ids:
        return []

    cli = AmadeusClient()
    params: Dict[str, str | int] = {
        "hotelIds": ",".join(hotel_ids),
        "adults": adults,
        "checkInDate": check_in,
        "checkOutDate": check_out,
        "currency": currency,
    }
    if best_rate_only:
        params["bestRateOnly"] = "true"

    payload: Dict = cli.get("/v3/shopping/hotel-offers", params)
    return payload.get("data", [])


def search_hotels(q: HotelQuery) -> Tuple[List[Dict], List[Dict]]:
    """
    High-level convenience:
      1) Get hotels for the city (Hotel List)
      2) Pick the first N hotelIds (q.max_hotels)
      3) Fetch offers for those IDs (Hotel Search v3)

    Returns:
      (offers, hotel_list)  -> both lists of dicts
      - offers: v3 items, each with "hotel" and "offers"[] (dynamic/availability)
      - hotel_list: list API items (static name/address/geo you can use to enrich)
    """
    hotel_list: List[Dict] = list_hotels_by_city(q.city_code)

    # Extract and trim hotelIds safely
    ids: List[str] = []
    for h in hotel_list:
        hid = h.get("hotelId") or h.get("hotel", {}).get("hotelId")
        if isinstance(hid, str) and hid:
            ids.append(hid)
        if len(ids) >= q.max_hotels:
            break

    offers: List[Dict] = search_hotel_offers_by_ids(
        hotel_ids=ids,
        check_in=q.check_in,
        check_out=q.check_out,
        adults=q.adults,
        currency=q.currency,
        best_rate_only=True,
    )
    return offers, hotel_list
