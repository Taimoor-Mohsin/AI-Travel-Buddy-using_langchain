from .base_agent import BaseAgent
from src.utils.logger import pretty_print
from dateutil import parser as dateparser
from datetime import datetime, timedelta


class ReminderAgent(BaseAgent):
    """
    Builds time-stamped reminders relative to the trip dates and itinerary.
    Output: list[ { "when": ISO8601, "message": str } ]
    """

    def _parse_date(self, s: str) -> datetime:
        # Lenient parse (handles "September 12th")
        # Default to 09:00 local time for general reminders
        dt = dateparser.parse(s, dayfirst=False, yearfirst=False, fuzzy=True)
        return dt.replace(hour=9, minute=0, second=0, microsecond=0)

    def run(self, input_data):
        if not input_data.trip_request:
            return {"reminders": [], "error": "No trip request provided"}

        tr = input_data.trip_request
        start = self._parse_date(tr.get("start_date", ""))
        end = self._parse_date(tr.get("end_date", ""))

        # Ensure start <= end
        if end < start:
            start, end = end, start

        prefs = tr.get("preferences", [])
        if isinstance(prefs, str):
            prefs = [prefs]

        # --- Core reminders (airport, check-in, pakcing etc.) ---
        reminders = []

        # T-7d: docs/insurance/passport check
        reminders.append(
            {
                "when": self._iso(start - timedelta(days=7)),
                "message": "Review passport/visa & travel insurance.",
            }
        )
        # T-3d: start packing
        reminders.append(
            {
                "when": self._iso(start - timedelta(days=3)),
                "message": "Start packing essentials (IDs, adapters, chargers).",
            }
        )
        # T-24h: online check‑in
        reminders.append(
            {
                "when": self._iso(start - timedelta(hours=24)),
                "message": "Online check‑in opens—pick seats and download boarding pass.",
            }
        )
        # T-6h: airport ride
        reminders.append(
            {
                "when": self._iso(start - timedelta(hours=6)),
                "message": "Confirm airport ride / ride-hailing availability.",
            }
        )
        # T-3h: leave for airport (intl buffer)
        reminders.append(
            {
                "when": self._iso(start - timedelta(hours=3)),
                "message": "Leave for airport (international flight buffer).",
            }
        )
        # --- Daily "today's plan" reminders mapped from itinerary ---
        itinerary = input_data.itinerary or []
        num_days = (end.date() - start.date()).days + 1
        for i in range(max(0, num_days)):
            day_dt = start + timedelta(days=i)
            if i < len(itinerary):
                msg = f"Today's plan: {itinerary[i]}"
            else:
                msg = "Free day / explore locally."
            # Schedule at 9 AM local by default
            remind_at = day_dt.replace(hour=9, minute=0, second=0, microsecond=0)
            reminders.append({"when": self._iso(remind_at), "message": msg})

            # Optional fun: dinner reminder at 19:00 with preference hint
            if prefs:
                dinner_dt = day_dt.replace(hour=19, minute=0, second=0, microsecond=0)
                reminders.append(
                    {
                        "when": self._iso(dinner_dt),
                        "message": f"Dinner idea near you (preferences: {', '.join(prefs)}).",
                    }
                )
        pretty_print("Reminders:", reminders)
        return {"reminders": reminders}

    def __call__(self, state):
        return self.run(state)

    def _iso(self, dt: datetime) -> str:
        """Convert datetime to ISO 8601 string."""
        return dt.isoformat()
