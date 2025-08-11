# 🧭 AI Travel Buddy — Multi-Agent Trip Planner (TEST API Build)

AI Travel Buddy is a LangChain/LangGraph-powered Streamlit app that uses
multiple agents to plan trips end-to-end.  
It takes structured trip details from the user, scrapes live-style TEST data
from Amadeus APIs for flights and hotels, and generates an itinerary, packing
list, and reminders.

> ⚠ **Note:** This build uses Amadeus Self-Service **Test Environment APIs**.
> Flight prices, availability, and hotel data are mock/test data — not
> production-live.

---

## ✨ Features

- **Structured Input UI** — enter Origin, Destination, Dates, Budget, and
  Preferences in separate fields.
- **Destination Pass-Through** — no LLM parsing needed if fields are filled;
  parser validates instead.
- **Flight Scraper (TEST)** — queries Amadeus Flight Offers API, returns:
  - Departure and arrival airport codes
  - Departure and arrival times
  - Number of stops
  - Airline IATA codes + full names
- **Hotel Scraper (TEST)** — uses Amadeus Hotel List + v3 Hotel Offers:
  - Cheapest available rate per hotel
  - Board type (e.g., ROOM_ONLY)
  - Check-in/check-out dates and nights
- **Budget Filtering** — Hotels filtered to ~15% of the total trip budget.
- **Multi-Agent Flow** — Supervisor coordinates:
  1. Destination parsing/validation
  2. Flight & hotel scraping
  3. Itinerary generation
  4. Packing list creation
  5. Reminder scheduling
- **Streamlit UI Tabs** for:
  - Trip Request
  - Flights & Hotels
  - Itinerary
  - Packing List
  - Reminders

---

## 📂 Project Structure

project_root/ │ ├── app.py # Streamlit app entry point ├── config/ # Config
files ├── data/ # Local data storage ├── src/ │ ├── agents/ # LangGraph agents │
│ ├── base_agent.py │ │ ├── destination_parser.py │ │ ├──
flight_hotel_scraper.py │ │ ├── itinerary_agent.py │ │ ├── packing_list_agent.py
│ │ ├── reminder_agent.py │ │ └── supervisor.py │ ├──
integrations/travel_scraper/ │ │ ├── amadeus_client.py │ │ ├── flights.py │ │
├── hotels.py │ │ ├── parsing.py │ │ ├── parsing_hotels.py │ │ └── reference.py
│ ├── schema/ │ │ └── travel_models.py │ └── utils/ │ ├── currency.py │ └──
logger.py ├── tests/ # Test scripts for individual modules ├── .env #
Environment variables (Amadeus keys etc.) ├── .gitignore # Ignore venv, .env,
pycache ├── requirements.txt └── README.md
