class MockElasticsearchClient:
    def get(self, params: dict, query: dict):
        return {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "contact_name": "John Doe",
                            "contact_urn": "1234567890",
                            "modified_on": "2025-01-01T00:00:00Z",
                        },
                        "values": [
                            {
                                "name": "test_op_field",
                                "value": "5",
                            },
                        ],
                    },
                ],
            },
        }
