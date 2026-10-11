import hashlib
import http.client
import json
import shutil
import subprocess
import time
from urllib.parse import urlsplit

from model_helpers import DECISION_URL, GPT_URL


def token(audience):
    executable = shutil.which("az") or shutil.which("az.cmd")
    if not executable:
        raise RuntimeError("Azure CLI is required. Install it and run az login.")
    result = subprocess.run(
        [executable, "account", "get-access-token", "--resource", audience, "-o", "json"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)["accessToken"]


class Session:
    def __init__(self, search_url="", gpt_pacing=4):
        for url in (DECISION_URL, GPT_URL):
            if urlsplit(url).scheme != "https" or not urlsplit(url).netloc:
                raise ValueError("Set DECISION_ENDPOINT and GPT_ENDPOINT to HTTPS model URLs.")
        if search_url and urlsplit(search_url).scheme != "https":
            raise ValueError("SEARCH_ENDPOINT must use HTTPS.")
        self.search_url = search_url
        self.gpt_pacing = gpt_pacing
        self.last_gpt = 0
        self.connections = {}
        self.bearers = {}

    def request(self, url, body=None):
        if url not in {DECISION_URL, GPT_URL, self.search_url}:
            raise ValueError("Request endpoint is not configured.")
        audience = "https://ai.azure.com" if url == self.search_url else "https://cognitiveservices.azure.com"
        if url == GPT_URL:
            time.sleep(max(0, self.last_gpt + self.gpt_pacing - time.monotonic()))
            self.last_gpt = time.monotonic()
        if audience not in self.bearers:
            self.bearers[audience] = token(audience)
        parts = urlsplit(url)
        path = parts.path + ("?" + parts.query if parts.query else "")
        encoded = json.dumps(body).encode() if body is not None else None
        started = time.perf_counter()
        attempts = []
        for attempt in range(2):
            connection = self.connections.setdefault(
                parts.netloc, http.client.HTTPSConnection(parts.netloc, timeout=90)
            )
            request_start = time.perf_counter()
            connection.request("POST" if body is not None else "GET", path, encoded, {
                "Authorization": "Bearer " + self.bearers[audience],
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            })
            response = connection.getresponse()
            raw = response.read().decode()
            attempts.append({"status": response.status,
                             "request_ms": (time.perf_counter() - request_start) * 1000})
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                events = [line[6:] for line in raw.splitlines() if line.startswith("data: ")]
                if not events:
                    raise RuntimeError(f"HTTP {response.status}: response is not JSON or an MCP event.")
                data = json.loads(events[-1])
            if response.status != 401 or attempt:
                break
            self.bearers[audience] = token(audience)
        return {
            "status": response.status, "response": data, "usage": data.get("usage", {}),
            "latency_ms": (time.perf_counter() - started) * 1000, "attempts": attempts,
            "request_sha256": hashlib.sha256(json.dumps(body).encode()).hexdigest(),
        }

    def close(self):
        for connection in self.connections.values():
            connection.close()
