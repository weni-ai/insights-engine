from unittest.mock import MagicMock


class MockElasticsearchClient:
    def __init__(self):
        self.get = MagicMock()

    def get(self, params: dict, query: dict):
        return MagicMock()
