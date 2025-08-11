from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel


class TripRequest(BaseModel):
    # NEW: let the UI pass the origin explicitly so we don't guess
    origin: Optional[str] = None
    destination: str
    start_date: str  # keep strings for now (easier with LLMs / JSON)
    end_date: str
    budget: Optional[float] = None
    preferences: Optional[Union[str, List[str]]] = None


class AccommodationOption(BaseModel):
    provider: str
    price: float
    details: Optional[str] = None


class FlightOption(BaseModel):
    airline: str
    price: float
    departure: str
    arrival: str


class TravelBuddyState(BaseModel):
    user_input: str
    home_iata: Optional[str] = None
    currency: Optional[str] = None
    trip_request: Optional[Dict[str, Any]] = None
    flight_options: Optional[List[Dict[str, Any]]] = None
    hotel_options: Optional[List[Dict[str, Any]]] = None
    itinerary: Optional[List[Any]] = None
    packing_list: Optional[List[str]] = None
    reminders: Optional[List[Dict[str, Any]]] = None
