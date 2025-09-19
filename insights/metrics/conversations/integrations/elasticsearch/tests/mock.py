from unittest.mock import MagicMock


class MockElasticsearchClient:
    def get(self, params: dict, query: dict):
        return MagicMock()

    def __init__(self):
        self.get = MagicMock()
