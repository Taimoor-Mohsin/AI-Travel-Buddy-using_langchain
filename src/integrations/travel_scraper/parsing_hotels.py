"""
parsing_hotels.py
-----------------
Turn Hotel Search v3 offers into clean summaries, and optionally ENRICH
them with static fields (name/address/geo) from the Hotel List API response.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime


# ---------- helpers unchanged (trimmed for brevity) ----------
def _safe_str(x: object) -> Optional[str]:
    return None if x is None else str(x)


def _nights_between(check_in: str | None, check_out: str | None) -> Optional[int]:
    try:
        if not check_in or not check_out:
            return None
        d1 = datetime.strptime(check_in, "%Y-%m-%d")
        d2 = datetime.strptime(check_out, "%Y-%m-%d")
        return max((d2 - d1).days, 0)
    except Exception:
        return None


def _cheapest_offer(hotel_item: Dict) -> Optional[Dict]:
    try:
        offers = hotel_item.get("offers", [])
        pairs = []
        for o in offers:
            total = o.get("price", {}).get("total")
            if total:
                try:
                    pairs.append((float(total), o))
                except Exception:
                    pass
        if not pairs:
            return None
        pairs.sort(key=lambda p: p[0])
        return pairs[0][1]
    except Exception:
        return None


# ---------- NEW: build a quick lookup from Hotel List ----------
def index_hotel_list(hotel_list: List[Dict]) -> Dict[str, Dict]:
    """
    Turn Hotel List items into {hotelId: static_info} for fast enrichment.
    """
    idx: Dict[str, Dict] = {}
    for h in hotel_list:
        hid = h.get("hotelId") or h.get("hotel", {}).get("hotelId")
        if not hid:
            continue
        idx[hid] = h
    return idx


def _address_from_list_item(item: Dict) -> Optional[str]:
    addr = item.get("address") or {}
    if not isinstance(addr, dict):
        return None
    line = None
    if isinstance(addr.get("lines"), list) and addr.get("lines"):
        line = addr.get("lines")[0]
    parts = [p for p in [line, addr.get("cityName"), addr.get("countryCode")] if p]
    return ", ".join(parts) if parts else None


def _geo_from_list_item(item: Dict) -> Optional[Dict]:
    try:
        lat = item.get("latitude")
        lng = item.get("longitude")
        if lat is None or lng is None:
            return None
        return {"lat": float(lat), "lng": float(lng)}
    except Exception:
        return None


# ---------- summaries ----------
def summarize_hotel_offer(
    v3_item: Dict, list_index: Dict[str, Dict] | None = None
) -> Dict[str, Any]:
    """
    v3_item: one element from /v3/shopping/hotel-offers "data" array.
      Expect a "hotel" sub-dict with at least hotelId and (often) name.
      Static details (address/geo) may be missing in v3, so we enrich from Hotel List when provided.

    Return: compact dict for UI.
    """
    hotel = v3_item.get("hotel", {}) or {}
    hid = hotel.get("hotelId")

    # BEST (cheapest) offer inside this v3 item
    cheap = _cheapest_offer(v3_item)

    # Start with whatever v3 gives us
    out: Dict[str, Any] = {
        "hotel_id": hid,
        "name": _safe_str(hotel.get("name")),
        "city_code": hotel.get("cityCode"),  # v3 still returns cityCode per item
        "address": None,  # might enrich below
        "geo": None,  # might enrich below
    }

    # Enrich with static info from Hotel List, if available
    if list_index and hid and hid in list_index:
        static = list_index[hid]
        out["name"] = out["name"] or _safe_str(static.get("name"))
        out["address"] = _address_from_list_item(static)
        out["geo"] = _geo_from_list_item(static)

    if cheap:
        price = cheap.get("price", {})
        ci = cheap.get("checkInDate")
        co = cheap.get("checkOutDate")
        out["cheapest"] = {
            "total": price.get("total"),
            "currency": price.get("currency"),
            "check_in": ci,
            "check_out": co,
            "nights": _nights_between(ci, co),
            "board": cheap.get("boardType")
            or (cheap.get("room", {}) or {}).get("boardType"),
        }
    else:
        out["cheapest"] = None

    return out


def summarize_hotels_offers(
    v3_items: List[Dict], hotel_list: List[Dict] | None = None
) -> List[Dict[str, Any]]:
    """
    Map all v3 items to summaries, enriched with Hotel List info when provided.
    Sort by cheapest price if available.
    """
    idx = index_hotel_list(hotel_list or [])

    def price_as_float(item: Dict) -> float:
        o = _cheapest_offer(item)
        try:
            return float(o.get("price", {}).get("total")) if o else float("inf")
        except Exception:
            return float("inf")

    v3_sorted = sorted(v3_items, key=price_as_float)
    return [summarize_hotel_offer(x, idx) for x in v3_sorted]
