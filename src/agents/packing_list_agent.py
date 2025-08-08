from .base_agent import BaseAgent
from src.utils.logger import pretty_print
import os
import requests
import json
import re

from dotenv import load_dotenv

load_dotenv()


class PackingListAgent(BaseAgent):
    def __call__(self, state):
        return self.run(state)

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")

    def call_groq_llm(
        self, destination: str, start_date: str, end_date: str, preferences
    ):
        if isinstance(preferences, list):
            pref_str = ", ".join(preferences)
        else:
            pref_str = preferences or "general sightseeing"

        # Strict JSON array request; no prose, no markdown.
        prompt = (
            "Generate a packing checklist as a STRICT JSON array of strings for the following trip. "
            "Do NOT include any explanations, markdown, or extra text—ONLY output a JSON array. "
            "Trip details:\n"
            f"- Destination: {destination}\n"
            f"- Dates: {start_date} to {end_date}\n"
            f"- Traveler preferences: {pref_str}\n\n"
            "Checklist should cover essentials (documents, chargers, adapters), weather-agnostic clothing basics, "
            'and a few items related to the preferences. Example format: ["Passport", "Phone charger", "..."] based on what may or may not be required'
        )
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 350,
            "temperature": 0.5,
        }
        resp = requests.post(url, headers=headers, json=payload)
        try:
            result = resp.json()
        except Exception as e:
            print("Error decoding JSON from Groq:", e)
            print("Raw response:", resp.text)
            raise RuntimeError(f"Groq did not return valid JSON: {resp.text}")

        if "choices" not in result:
            print("Groq API Error:", result)
            raise RuntimeError(f"Groq API returned error: {result}")

        return result["choices"][0]["message"]["content"]

    def run(self, input_data):
        # Expect prior agents to have filled trip_request (and optionally itinerary)
        if not input_data.trip_request:
            return {"packing_list": [], "error": "No trip request provided."}

        tr = input_data.trip_request
        destination = tr.get("destination", "the destination")
        start_date = tr.get("start_date", "")
        end_date = tr.get("end date", "")
        preferences = tr.get("preferences", [])

        llm_output = self.call_groq_llm(destination, start_date, end_date, preferences)
        # print("Raw Debugging output (packing_list_agent):", llm_output)  #

        # Extract JSON array
        json_match = re.search(r"\[.*\]", llm_output, re.DOTALL)
        if not json_match:
            print("Could not find packing list JSON in LLM output!")
            return {"packing_list": [], "error": "No packing JSON found in LLM output"}

        try:
            packing_list = json.loads(json_match.group(0))
            # Light Normalization: ensure list[str]
            packing_list = [
                str(item).strip() for item in packing_list if str(item).strip()
            ]
            pretty_print("Packing List:", packing_list)
            return {"packing_list": packing_list}
        except Exception as e:
            print("Error parsing packing JSON:", e)
            return {"packing_list": [], "error": str(e)}
