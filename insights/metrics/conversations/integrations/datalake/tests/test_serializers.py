import uuid
from django.test import TestCase

from insights.metrics.conversations.integrations.datalake.serializers import (
    TopicsRelationsSerializer,
    TopicsBaseStructureSerializer,
    TopicsDistributionSerializer,
)


class TestTopicsRelationsSerializer(TestCase):
    def test_serialize(self):
        topics_list = [
            {
                "uuid": str(uuid.uuid4()),
                "name": "Test Topic",
                "subtopic": [
                    {
                        "uuid": str(uuid.uuid4()),
                        "name": "Test Subtopic",
                    }
                ],
            },
            {
                "uuid": str(uuid.uuid4()),
                "name": "Test Topic 2",
                "subtopic": [],
            },
        ]

        serializer = TopicsRelationsSerializer(topics_list)
        expected_result = {
            str(topics_list[0]["uuid"]): {
                "name": topics_list[0]["name"],
                "uuid": str(topics_list[0]["uuid"]),
                "subtopics": {
                    str(topics_list[0]["subtopic"][0]["uuid"]): {
                        "name": topics_list[0]["subtopic"][0]["name"],
                        "uuid": str(topics_list[0]["subtopic"][0]["uuid"]),
                    }
                },
            },
            str(topics_list[1]["uuid"]): {
                "name": topics_list[1]["name"],
                "uuid": str(topics_list[1]["uuid"]),
                "subtopics": {},
            },
        }

        self.assertEqual(
            serializer.data,
            expected_result,
        )
