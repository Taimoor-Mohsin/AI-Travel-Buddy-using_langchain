from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel


class TripRequest(BaseModel):
    destination: str
    start_date: str  # We'll use string for dates for now (easier for LLM output)
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
    trip_request: Optional[Dict[str, Any]] = None
    flight_options: Optional[List[Dict[str, Any]]] = None
    hotel_options: Optional[List[Dict[str, Any]]] = None
    itinerary: Optional[List[str]] = None
    packing_list: Optional[List[str]] = None
