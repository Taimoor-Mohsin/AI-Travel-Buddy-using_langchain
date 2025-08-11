"""
parsing.py
-----------
Pure parsing utilities for Amadeus Flight Offers JSON.

This module NEVER calls the network. It only:
  • extracts fields from raw Amadeus offer dicts (safe .get(...) everywhere)
  • groups offers by airports
  • builds tidy summaries for UI display (airports, times, price, carriers)

You can unit-test everything here without hitting the API.

Typical usage (in tests or your app layer):
    from .flights import FlightQuery, search_flights
    from .reference import city_to_codes
    from .parsing import summarize_offers_airports_and_carriers

    codes = city_to_codes("Rome")             # {'city': 'ROM', 'airport': 'FCO'}
    offers = search_flights(FlightQuery(
        origin_iata="LHE",
        dest_iata=codes["city"],
        depart_date="2025-09-12",
        return_date="2025-09-17",
        adults=1,
        currency="USD",
        max_results=20,
        travel_class="ECONOMY",
    ))
    summaries = summarize_offers_airports_and_carriers(offers)
"""

from __future__ import annotations  # postpone type evaluation (cleaner forward refs)

from typing import Any, Callable, DefaultDict, Dict, List, Optional
from collections import defaultdict

# --- Optional import: airline name lookup (uses Amadeus /v1/reference-data/airlines)
# If you haven't created airlines.py yet, the fallback returns {} and names will show as "Unknown Airline".
try:
    from .airlines import map_airline_codes_to_names
except Exception:  # pragma: no cover - only hit if airlines.py missing during dev

    def map_airline_codes_to_names(_codes: List[str]) -> Dict[str, str]:
        """Fallback: no names available."""
        return {}


# =============================================================================
# Low-level safe extractors (single-value helpers)
# =============================================================================


def get_outbound_departure_airport(offer: Dict) -> Optional[str]:
    """
    Returns the IATA code of the DEPARTURE airport for the FIRST (outbound) itinerary.

    Typical shape:
      offer["itineraries"][0]["segments"][0]["departure"]["iataCode"]  -> "LHR"

    Returns:
        str | None
    """
    try:
        return (
            offer.get("itineraries", [])[0]
            .get("segments", [])[0]
            .get("departure", {})
            .get("iataCode")
        )
    except Exception:
        return None


def get_outbound_arrival_airport(offer: Dict) -> Optional[str]:
    """
    Returns the IATA code of the FINAL ARRIVAL airport for the FIRST (outbound) itinerary.

    We take the LAST segment of itinerary[0]:
      offer["itineraries"][0]["segments"][-1]["arrival"]["iataCode"]  -> "FCO"

    Returns:
        str | None
    """
    try:
        segs = offer.get("itineraries", [])[0].get("segments", [])
        if not segs:
            return None
        return segs[-1].get("arrival", {}).get("iataCode")
    except Exception:
        return None


def get_total_price(offer: Dict) -> Optional[float]:
    """
    Parses price.grandTotal (string like '933.00') into float for sorting/filtering.

    Returns:
        float | None
    """
    try:
        return float(offer.get("price", {}).get("grandTotal"))
    except Exception:
        return None


def get_currency(offer: Dict) -> Optional[str]:
    """
    Returns the currency code reported by Amadeus (e.g., 'USD').

    Returns:
        str | None
    """
    return offer.get("price", {}).get("currency")


# =============================================================================
# Generic grouping utilities
# =============================================================================


def group_offers_by(
    offers: List[Dict], key_fn: Callable[[Dict], Optional[str]]
) -> Dict[str, List[Dict]]:
    """
    Groups a list of offers into buckets keyed by key_fn(offer).

    Args:
        offers: list of raw Amadeus offers (dicts)
        key_fn: function that returns a key (e.g., "FCO") or None

    Returns:
        dict[str, list[dict]]  -> {"FCO": [...], "CIA": [...], "UNKNOWN": [...]}
    """
    buckets: DefaultDict[str, List[Dict]] = defaultdict(list)
    for o in offers:
        k = key_fn(o) or "UNKNOWN"
        buckets[k].append(o)
    return dict(buckets)


def group_by_outbound_arrival_airport(offers: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Buckets by final ARRIVAL airport of the outbound leg (itinerary[0]).
    Useful when destination is a CITY code (e.g., ROM → FCO/CIA).
    """
    return group_offers_by(offers, get_outbound_arrival_airport)


def group_by_outbound_departure_airport(offers: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Buckets by DEPARTURE airport of the outbound leg.
    Useful when ORIGIN is a CITY code (e.g., LON → LHR/LGW/LCY/STN/LTN/SEN).
    """
    return group_offers_by(offers, get_outbound_departure_airport)


# =============================================================================
# Mid-level helpers: working with itineraries/segments
# =============================================================================


def _first_segment(offer: Dict, itin_index: int) -> Optional[Dict]:
    """
    Returns the first segment dict of itinerary[itin_index], or None.

    Args:
        offer: raw Amadeus offer (dict)
        itin_index: 0 for outbound, 1 for inbound (if present)

    Returns:
        dict | None
    """
    try:
        return offer.get("itineraries", [])[itin_index].get("segments", [])[0]
    except Exception:
        return None


def _last_segment(offer: Dict, itin_index: int) -> Optional[Dict]:
    """
    Returns the last segment dict of itinerary[itin_index], or None.

    We use this to get the final arrival airport/time of a leg.
    """
    try:
        segs = offer.get("itineraries", [])[itin_index].get("segments", [])
        return segs[-1] if segs else None
    except Exception:
        return None


def _leg_airport_times(offer: Dict, itin_index: int) -> Dict[str, Optional[str]]:
    """
    Extracts a single leg's from/to airport codes and timestamps.

    Returns a dict with keys:
      - from_airport (str|None)
      - to_airport   (str|None)
      - depart_time  (str|None, ISO 'YYYY-MM-DDTHH:MM:SS')
      - arrive_time  (str|None)
      - stops        (int|None)  number of connections = segments-1
    """
    try:
        itins = offer.get("itineraries", [])
        if len(itins) <= itin_index:
            return {
                "from_airport": None,
                "to_airport": None,
                "depart_time": None,
                "arrive_time": None,
                "stops": None,
            }

        segments: List[Dict] = itins[itin_index].get("segments", [])
        if not segments:
            return {
                "from_airport": None,
                "to_airport": None,
                "depart_time": None,
                "arrive_time": None,
                "stops": 0,
            }

        first = segments[0]
        last = segments[-1]
        return {
            "from_airport": first.get("departure", {}).get("iataCode"),
            "to_airport": last.get("arrival", {}).get("iataCode"),
            "depart_time": first.get("departure", {}).get("at"),
            "arrive_time": last.get("arrival", {}).get("at"),
            "stops": max(len(segments) - 1, 0),
        }
    except Exception:
        # Defensive default on any unexpected shape
        return {
            "from_airport": None,
            "to_airport": None,
            "depart_time": None,
            "arrive_time": None,
            "stops": None,
        }


def _carrier_codes_for_leg(offer: Dict, itin_index: int) -> List[str]:
    """
    Collect unique carrier codes for a specific leg (outbound=0, inbound=1).
    Prefer the operating carrier when present; fall back to marketing carrier.
    """
    try:
        segs = offer.get("itineraries", [])[itin_index].get("segments", [])
        codes_in_order = []
        seen = set()
        for s in segs:
            op = (s.get("operating") or {}).get("carrierCode")
            mk = s.get("carrierCode")
            code = op or mk
            if code and code not in seen:
                seen.add(code)
                codes_in_order.append(code)
        return codes_in_order
    except Exception:
        return []


# =============================================================================
# High-level: summaries for UI (airports/times/price[/carriers])
# =============================================================================


def summarize_offer_airports(offer: Dict) -> Dict[str, Any]:
    """
    Tidy dict for UI showing:
      - offer id, price, currency
      - outbound leg (from_airport → to_airport, times, stops)
      - inbound  leg if present

    Returns:
        dict[str, Any]
    """
    outbound = _leg_airport_times(offer, 0)  # first itinerary = outbound
    inbound = _leg_airport_times(
        offer, 1
    )  # second itinerary = inbound (may be missing)

    price_block = offer.get("price", {})  # dict
    return {
        "id": offer.get("id"),  # str|None
        "price_total": price_block.get("grandTotal"),  # str|None (e.g., "933.00")
        "currency": price_block.get("currency"),  # str|None (e.g., "USD")
        "outbound": outbound,  # dict
        "inbound": inbound if inbound["from_airport"] else None,  # dict|None
    }


def summarize_offers_airports(offers: List[Dict]) -> List[Dict[str, Any]]:
    """
    Maps a list of offers to airport summaries, sorted by numeric price if present.
    """

    def price_as_float(o: Dict) -> float:
        try:
            return float(o.get("price", {}).get("grandTotal"))
        except Exception:
            return float("inf")

    sorted_offers = sorted(offers, key=price_as_float)
    return [summarize_offer_airports(o) for o in sorted_offers]


def summarize_offer_airports_and_carriers(offer: Dict) -> Dict[str, Any]:
    """
    Airport summary + carriers (codes and resolved names) per leg.

    Requires airlines.map_airline_codes_to_names() to resolve names. If that
    import failed, names will be "Unknown Airline" via fallback.
    """
    outbound = _leg_airport_times(offer, 0)
    inbound = _leg_airport_times(offer, 1)

    out_codes = _carrier_codes_for_leg(offer, 0)
    in_codes = _carrier_codes_for_leg(offer, 1) if inbound["from_airport"] else []

    # Lookup airline names in one batch call (dedup codes first)
    names_map = map_airline_codes_to_names(list({*out_codes, *in_codes}))

    def with_names(codes: List[str]) -> List[str]:
        # always returns something (e.g., "XX — Unknown Airline") if lookup fails
        return [f"{c} — {names_map.get(c, 'Unknown Airline')}" for c in codes]

    price_block = offer.get("price", {})
    return {
        "id": offer.get("id"),
        "price_total": price_block.get("grandTotal"),
        "currency": price_block.get("currency"),
        "outbound": {
            **outbound,
            "carriers": out_codes,  # e.g., ["QR"]
            "carrier_names": with_names(out_codes),  # e.g., ["QR — Qatar Airways"]
        },
        "inbound": (
            None
            if not inbound["from_airport"]
            else {
                **inbound,
                "carriers": in_codes,
                "carrier_names": with_names(in_codes),
            }
        ),
    }


def summarize_offers_airports_and_carriers(offers: List[Dict]) -> List[Dict[str, Any]]:
    """
    Batch version of the above; sorts by numeric price for stable display.
    """

    def price_as_float(o: Dict) -> float:
        try:
            return float(o.get("price", {}).get("grandTotal"))
        except Exception:
            return float("inf")

    offers_sorted = sorted(offers, key=price_as_float)
    return [summarize_offer_airports_and_carriers(o) for o in offers_sorted]
