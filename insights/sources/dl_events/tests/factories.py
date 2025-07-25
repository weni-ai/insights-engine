import factory
import pendulum
import uuid
import random
from faker import Faker

faker = Faker()


class ClassificationEventFactory(factory.Factory):
    class Meta:
        model = dict

    project_uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    contact_urn = factory.LazyFunction(lambda: faker.numerify(text="##########"))
    classification_name = factory.LazyFunction(
        lambda: random.choice(["resolved", "unresolved", "abandoned"])
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return {
            "event_name": "weni_nexus_data",
            "key": "conversation_classification",
            "value": kwargs.get("classification_name", cls.classification_name),
            "date": pendulum.now("America/Sao_Paulo").to_iso8601_string(),
            "project": kwargs.get("project_uuid", cls.project_uuid),
            "contact_urn": kwargs.get("contact_urn", cls.contact_urn),
            "value_type": "string",
            "metadata": {},
        }


class TopicsEventFactory(factory.Factory):
    class Meta:
        model = dict

    project_uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    contact_urn = factory.LazyFunction(lambda: faker.numerify(text="##########"))
    classification_name = factory.LazyFunction(
        lambda: random.choice(["topic1", "topic2", "topic3", "bias"])
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return {
            "event_name": "weni_nexus_data",
            "key": "topics",
            "value": kwargs.get("classification_name", cls.classification_name),
            "date": pendulum.now("America/Sao_Paulo").to_iso8601_string(),
            "project": kwargs.get("project_uuid", cls.project_uuid),
            "contact_urn": kwargs.get("contact_urn", cls.contact_urn),
            "value_type": "string",
            "metadata": {
                "topic_uuid": str(uuid.uuid4()),
                "subtopic_uuid": random.choice([str(uuid.uuid4()), None]),
                "subtopic": random.choice(
                    ["subtopic1", "subtopic2", "subtopic3", "bias"]
                ),
            },
        }
