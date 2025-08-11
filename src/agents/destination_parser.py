# src/agents/destination_parser.py
from dotenv import load_dotenv
from .base_agent import BaseAgent
from src.schema.travel_models import TripRequest
from src.utils.logger import pretty_print
import os, requests, json, re

load_dotenv()


class DestinationParserAgent(BaseAgent):
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")

    def __call__(self, state):
        return self.run(state)

    def call_groq_llm(self, user_input):
        # (unchanged) … kept for fallback when user types a single prompt
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        prompt = (
            "Extract the following fields from the user's travel request and output them as strict JSON (no explanations, no markdown, no comments): "
            "origin, destination, start_date, end_date, budget, preferences. "
            "If a field is not mentioned, set it to null. "
            f'User input: "{user_input}"\nJSON:'
        )
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.0,
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        if "choices" not in result:
            raise RuntimeError(f"Groq API returned error: {result}")
        return result["choices"][0]["message"]["content"]

    def run(self, input_data):
        """
        Pass-through mode:
          - If input_data.trip_request already contains structured fields, validate and return it.
        Fallback mode:
          - Else, parse free-text input (user_input) with the LLM and return TripRequest.
        """
        # ---------- Pass-through ----------
        tr_dict = getattr(input_data, "trip_request", None)
        if (
            isinstance(tr_dict, dict)
            and tr_dict.get("destination")
            and tr_dict.get("start_date")
            and tr_dict.get("end_date")
        ):
            try:
                # Normalize preferences to list-of-str when possible
                trip = TripRequest(**tr_dict)
                if isinstance(trip.preferences, str):
                    trip.preferences = [trip.preferences]
                pretty_print("Trip Request (pass-through)", trip.dict())
                return {"trip_request": trip.dict()}
            except Exception as e:
                # Fall through to parsing if prefilled values were malformed
                print("Pass-through TripRequest validation failed:", e)

        # ---------- Fallback: parse free text ----------
        user_input = input_data.user_input
        llm_output = self.call_groq_llm(user_input)
        json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
        if not json_match:
            return {"trip_request": None, "error": "No JSON found in LLM output"}

        try:
            trip_dict = json.loads(json_match.group(0))
            trip = TripRequest(**trip_dict)
            if isinstance(trip.preferences, str):
                trip.preferences = [trip.preferences]
            pretty_print("Trip Request (parsed)", trip.dict())
            return {"trip_request": trip.dict()}
        except Exception as e:
            return {"trip_request": None, "error": str(e)}
