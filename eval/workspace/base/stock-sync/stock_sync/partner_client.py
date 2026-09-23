"""HTTP client for the marketplace partner API. All partner calls go through _request."""
import json
import logging
import time
import urllib.error
import urllib.request

from . import config

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {500, 502, 503, 504}


class PartnerError(Exception):
    pass


class PartnerClient:
    def __init__(self, base_url=None, token=None, timeout=None, max_retries=None, opener=None):
        self.base_url = (base_url or config.PARTNER_BASE_URL).rstrip("/")
        self.token = token if token is not None else config.PARTNER_TOKEN
        self.timeout = timeout or config.PARTNER_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else config.PARTNER_MAX_RETRIES
        self._open = opener or urllib.request.urlopen

    def _request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        for attempt in range(self.max_retries + 1):
            try:
                with self._open(req, timeout=self.timeout) as resp:
                    return resp.status, resp.read()
            except urllib.error.HTTPError as e:
                if e.code not in RETRYABLE_STATUS or attempt == self.max_retries:
                    raise PartnerError(f"{method} {path} failed: {e.code}") from e
            except urllib.error.URLError as e:
                if attempt == self.max_retries:
                    raise PartnerError(f"{method} {path} failed: {e.reason}") from e
            time.sleep(2 ** attempt)

    def send_inventory(self, items):
        status, _ = self._request("POST", "/v2/inventory", {"items": items})
        log.debug("partner inventory call returned %s for %d items", status, len(items))
        return status
