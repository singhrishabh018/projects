"""Fake partner endpoint for tests: records requests, answers 202 like the real API."""
import io
import json


class FakeResponse(io.BytesIO):
    def __init__(self, status=202, body=b"{}"):
        super().__init__(body)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakePartner:
    def __init__(self):
        self.requests = []

    def __call__(self, req, timeout=None):
        body = json.loads(req.data) if req.data else None
        self.requests.append({"method": req.get_method(), "url": req.full_url, "body": body})
        return FakeResponse(202)
