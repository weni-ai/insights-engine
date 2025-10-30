class TopicsRelationsSerializer:
    """
    Topics relations serializer
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

            if subtopics_list == []:
                relations[topic_uuid]["subtopics"]["OTHER"] = {
                    "name": "Other",
                    "uuid": None,
                }
            else:
                for subtopic in subtopics_list:
                    subtopic_uuid = subtopic.get("uuid")
                    subtopic_name = subtopic.get("name")

                    relations[topic_uuid]["subtopics"][subtopic_uuid] = {
                        "name": subtopic_name,
                        "uuid": subtopic_uuid,
                    }
            
        return relations



class TopicsBaseStructureSerializer:
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
        
        



class TopicsDistributionSerializer:
    """
    Serializer for topics distribution
    """

    def __init__(self, topics_d)