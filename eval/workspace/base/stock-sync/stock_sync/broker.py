"""Thin wrapper around the message broker client (the real client is injected in prod)."""


class Broker:
    def __init__(self, client):
        self._client = client

    def subscribe(self, topic, group):
        return self._client.subscribe(topic, group=group)

    def commit(self, message):
        self._client.commit(message)

    def publish(self, topic, value):
        self._client.publish(topic, value)
