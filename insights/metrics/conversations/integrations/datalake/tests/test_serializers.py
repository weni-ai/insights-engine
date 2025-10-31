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


class TestTopicsBaseStructureSerializer(TestCase):
    def test_serialize(self):
        topic_1_uuid = str(uuid.uuid4())
        topic_2_uuid = str(uuid.uuid4())

        subtopic_1_uuid = str(uuid.uuid4())

        topics_relations = {
            topic_1_uuid: {
                "name": "Test Topic",
                "uuid": topic_1_uuid,
                "subtopics": {
                    subtopic_1_uuid: {
                        "name": "Test Subtopic",
                        "uuid": subtopic_1_uuid,
                    },
                },
            },
            topic_2_uuid: {
                "name": "Test Topic 2",
                "uuid": topic_2_uuid,
                "subtopics": {},
            },
        }
        serializer = TopicsBaseStructureSerializer(topics_relations, "Unclassified")
        expected_result = {
            "OTHER": {
                "name": "Unclassified",
                "uuid": None,
                "count": 0,
                "subtopics": {},
            },
        }
        expected_result[topic_1_uuid] = {
            "name": "Test Topic",
            "uuid": topic_1_uuid,
            "count": 0,
            "subtopics": {
                subtopic_1_uuid: {
                    "name": "Test Subtopic",
                    "uuid": subtopic_1_uuid,
                    "count": 0,
                },
                "OTHER": {
                    "name": "Unclassified",
                    "uuid": None,
                    "count": 0,
                },
            },
        }
        expected_result[topic_2_uuid] = {
            "name": "Test Topic 2",
            "uuid": topic_2_uuid,
            "count": 0,
            "subtopics": {
                "OTHER": {
                    "name": "Unclassified",
                    "uuid": None,
                    "count": 0,
                },
            },
        }

        self.assertEqual(serializer.data, expected_result)


class TestTopicsDistributionSerializer(TestCase):
    def test_serialize(self):
        topic_1_uuid = str(uuid.uuid4())
        topic_2_uuid = str(uuid.uuid4())
        unknown_topic_1_uuid = str(uuid.uuid4())

        subtopic_1_uuid = str(uuid.uuid4())
        unknown_subtopic_1_uuid = str(uuid.uuid4())
        unknown_subtopic_2_from_topic_1_uuid = str(uuid.uuid4())

        topics_list = [
            {
                "uuid": topic_1_uuid,
                "name": "Test Topic",
                "subtopic": [
                    {
                        "uuid": subtopic_1_uuid,
                        "name": "Test Subtopic",
                    }
                ],
            },
            {
                "uuid": topic_2_uuid,
                "name": "Test Topic 2",
                "subtopic": [],
            },
        ]

        topics_relations = TopicsRelationsSerializer(topics_list).data
        base_structure = TopicsBaseStructureSerializer(
            topics_relations, "Unclassified"
        ).data

        topics_events = [
            {
                "group_value": topic_1_uuid,
                "count": 60,
            },
            {
                "group_value": topic_2_uuid,
                "count": 20,
            },
            {
                # Unknown topic, should be considered as unclassified.
                "group_value": unknown_topic_1_uuid,
                "count": 30,
            },
            {
                # Empty topic UUID, should be considered as unclassified.
                "group_value": None,
                "count": 40,
            },
        ]

        subtopics_events = [
            {
                "group_value": subtopic_1_uuid,
                "count": 10,
            },
            {
                # Unknown subtopic, should be considered as unclassified.
                "group_value": unknown_subtopic_1_uuid,
                "count": 40,
            },
            {
                # Unknown subtopic from topic 1, should be considered as unclassified
                # inside topic 1.
                "group_value": unknown_subtopic_2_from_topic_1_uuid,
                "count": 50,
            },
        ]

        serializer = TopicsDistributionSerializer(
            topics_relations, base_structure, topics_events, subtopics_events
        )
        data = serializer.data

        self.assertEqual(data["OTHER"]["count"], 70)

        self.assertEqual(data[topic_1_uuid]["count"], 60)
        self.assertEqual(data[topic_1_uuid]["subtopics"][subtopic_1_uuid]["count"], 10)
        self.assertEqual(data[topic_1_uuid]["subtopics"]["OTHER"]["count"], 50)

        self.assertEqual(data[topic_2_uuid]["count"], 20)
        self.assertEqual(data[topic_2_uuid]["subtopics"]["OTHER"]["count"], 20)
