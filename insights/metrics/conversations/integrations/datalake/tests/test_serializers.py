import json
import uuid
from django.test import TestCase

from insights.metrics.conversations.integrations.datalake.serializers import (
    CrosstabLabelsSerializer,
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


class TestCrosstabLabelsSerializer(TestCase):
    def setUp(self) -> None:
        self.serializer_class = CrosstabLabelsSerializer
        self.events_source_a = [
            {
                "event_name": "weni_nexus_data",
                "key": "value",
                "value": "value1",
                "date": 1716883200,
                "contact_urn": "1234567890",
                "value_type": "string",
                "metadata": json.dumps(
                    {
                        "conversation_uuid": "1234567890",
                        "metadata_abc": "value3",
                    }
                ),
            },
            {
                "event_name": "weni_nexus_data",
                "key": "value",
                "value": "value2",
                "date": 1716883200,
                "contact_urn": "1234567891",
                "value_type": "string",
                "metadata": json.dumps(
                    {
                        "conversation_uuid": "1234567891",
                        "metadata_abc": "value4",
                    }
                ),
            },
        ]

    def test_serialize(self):
        serializer = self.serializer_class(self.events_source_a, "value")
        data = serializer.serialize()

        self.assertEqual(data["labels"], {"value1", "value2"})
        self.assertEqual(
            data["conversations_uuids"],
            {"1234567890": "value1", "1234567891": "value2"},
        )

    def test_serialize_with_metadata_key(self):
        serializer = self.serializer_class(self.events_source_a, "metadata_abc")
        data = serializer.serialize()

        self.assertEqual(data["labels"], {"value3", "value4"})
        self.assertEqual(
            data["conversations_uuids"],
            {"1234567890": "value3", "1234567891": "value4"},
        )
