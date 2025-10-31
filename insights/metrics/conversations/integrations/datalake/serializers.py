from abc import ABC, abstractmethod


class AbstractSerializer(ABC):

    @abstractmethod
    def serialize(self) -> dict:
        raise NotImplementedError("Subclasses must implement this method")


class BaseSerializer(AbstractSerializer):
    """
    Base serializer class
    """

    @property
    def data(self) -> dict:
        """
        Get the serialized data
        """
        return self.serialize()


class TopicsRelationsSerializer(BaseSerializer):
    """
    Topics relations serializer

    This is used to get the relations between topics and subtopics,
    through a dict mapping topic UUIDs to their name and subtopics.

    These topics and subtopics were previously created by the project's
    users and are retrieved by Insights from Nexus.

    Only these topics and subtopics should be returned to the frontend app,
    any other topic or subtopic is considered as unclassified.
    """

    def __init__(self, topics_list: list[dict]):
        self.topics_list = topics_list

    def serialize(self) -> dict:
        """
        Serialize topics list to relations.
        """
        relations = {}

        for topic in self.topics_list:
            topic_uuid = topic.get("uuid")
            topic_name = topic.get("name")

            subtopics_list = topic.get("subtopic", [])

            relations[topic_uuid] = {
                "name": topic_name,
                "uuid": topic_uuid,
                "subtopics": {},
            }
            for subtopic in subtopics_list:
                subtopic_uuid = subtopic.get("uuid")
                subtopic_name = subtopic.get("name")

                relations[topic_uuid]["subtopics"][subtopic_uuid] = {
                    "name": subtopic_name,
                    "uuid": subtopic_uuid,
                }

        return relations


class TopicsBaseStructureSerializer(BaseSerializer):
    """
    Topics base structure serializer
    """

    def __init__(self, topics_relations: dict, unclassified_label: str):
        self.topics_relations = topics_relations
        self.unclassified_label = unclassified_label

    def serialize(self) -> dict:
        """
        Serialize topics list to base structure.
        """
        # When an event has not a classified topic or a topic is not present in the topics relations
        # it is considered as unclassified.
        base_structure = {
            "OTHER": {
                "name": self.unclassified_label,
                "uuid": None,
                "count": 0,
                "subtopics": {},
            }
        }

        for topic_uuid, topic_data in self.topics_relations.items():
            subtopics = {}

            for subtopic_uuid, subtopic_data in topic_data["subtopics"].items():
                subtopics[subtopic_uuid] = {
                    "name": subtopic_data.get("name"),
                    "uuid": subtopic_uuid,
                    "count": 0,
                }

            subtopics["OTHER"] = {
                "name": self.unclassified_label,
                "uuid": None,
                "count": 0,
            }

            base_structure[topic_uuid] = {
                "name": topic_data.get("name"),
                "uuid": topic_uuid,
                "count": 0,
                "subtopics": subtopics,
            }

        return base_structure


class TopicsDistributionSerializer(BaseSerializer):
    """
    Serializer for topics distribution
    """

    def __init__(
        self,
        relations: dict,
        base_structure: dict,
        topics_events: list[dict],
        subtopics_events: list[dict],
    ):
        self.relations = relations
        self.base_structure = base_structure
        self.topics_events = topics_events
        self.subtopics_events = subtopics_events

        self.topics_data = base_structure.copy()

    def _serialize_topics_events(self) -> None:
        """
        Serialize topics events to list.
        """
        for topic_event in self.topics_events:
            topic_uuid = topic_event.get("group_value")

            if topic_uuid in {"", None} or topic_uuid not in self.relations:
                # If the topic UUID is unknown or not present in the relations,
                # it is considered as unclassified.
                self.topics_data["OTHER"]["count"] += topic_event.get("count", 0)
            else:
                # If the topic UUID is present in the relations,
                # it is considered as classified.
                topic_count = topic_event.get("count", 0)

                if topic_count == 0:
                    del self.topics_data[topic_uuid]
                else:
                    self.topics_data[topic_uuid]["count"] += topic_count

    def _get_subtopics_relations(self) -> dict:
        """
        Get subtopics relations from relations.
        """

        subtopics_relations = {}

        for topic_uuid, topic_data in self.relations.items():
            for subtopic_uuid, subtopic_data in topic_data["subtopics"].items():
                subtopics_relations[subtopic_uuid] = {
                    "name": subtopic_data.get("name"),
                    "uuid": subtopic_uuid,
                    "topic_uuid": topic_uuid,
                }

        return subtopics_relations

    def _serialize_subtopics_events(self) -> None:
        """
        Serialize subtopics events to list.
        """

        subtopics_relations = self._get_subtopics_relations()

        for subtopic_event in self.subtopics_events:
            subtopic_uuid = subtopic_event.get("group_value")

            if subtopic_uuid in {"", None}:
                continue

            subtopic_data = subtopics_relations.get(subtopic_uuid, {})

            if not subtopic_data:
                continue

            subtopic_count = subtopic_event.get("count", 0)
            topic_uuid = subtopic_data.get("topic_uuid")

            if subtopic_count == 0:
                del self.topics_data[topic_uuid]["subtopics"][subtopic_uuid]
                continue

            if subtopic_uuid in self.topics_data[topic_uuid]["subtopics"]:
                self.topics_data[topic_uuid]["subtopics"][subtopic_uuid][
                    "count"
                ] += subtopic_count

    def _calculate_topics_other_count(self) -> None:
        """
        Calculate topics other count.
        """
        for topic_uuid, topic_data in self.topics_data.items():
            topic_count = topic_data.get("count", 0)

            if topic_count == 0:
                del self.topics_data[topic_uuid]
                continue

            if topic_uuid == "OTHER":
                continue

            subtopics_count = sum(
                subtopic_data.get("count", 0)
                for subtopic_data in topic_data["subtopics"].values()
            )

            other_count = topic_count - subtopics_count
            self.topics_data[topic_uuid]["subtopics"]["OTHER"]["count"] = other_count

    def serialize(self) -> dict:
        """
        Serialize topics distribution to list.
        """
        self._serialize_topics_events()
        self._serialize_subtopics_events()
        self._calculate_topics_other_count()

        return self.topics_data
