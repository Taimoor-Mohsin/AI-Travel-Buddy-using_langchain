# amadeus_client.py
import os, time, requests
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()

API_KEY = os.getenv("AMADEUS_API_KEY")
API_SECRET = os.getenv("AMADEUS_API_SECRET")
ENV = (os.getenv("AMADEUS_ENV") or "test").lower()

BASE_URL = (
    "https://test.api.amadeus.com" if ENV == "test" else "https://api.amadeus.com"
)


class AmadeusError(Exception):
    pass


class AmadeusClient:
    def __init__(
        self,
        api_key: str = API_KEY,
        api_secret: str = API_SECRET,
        base_url: str = BASE_URL,
    ):
        if not api_key or not api_secret:
            raise ValueError("AMADEUS_API_KEY/SECRET missing")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self._token: Optional[str] = None
        self._exp: float = 0

    def _need_token(self) -> bool:
        return not self._token or time.time() >= self._exp - 30

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(1, 2, 8),
        retry=retry_if_exception_type(AmadeusError),
    )
    def _refresh_token(self):
        url = f"{self.base_url}/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(url, data=data, headers=headers, timeout=20)
        if r.status_code != 200:
            raise AmadeusError(f"OAuth failed: {r.status_code} {r.text}")
        payload = r.json()
        self._token = payload["access_token"]
        self._exp = time.time() + int(payload.get("expires_in", 1799))

    def _auth_header(self) -> Dict[str, str]:
        if self._need_token():
            self._refresh_token()
        return {"Authorization": f"Bearer {self._token}"}

    def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        r = requests.get(
            f"{self.base_url}{path}",
            headers=self._auth_header(),
            params=params,
            timeout=30,
        )
        if r.status_code >= 400:
            raise AmadeusError(f"GET {path} failed: {r.status_code} {r.text}")
        return r.json()
