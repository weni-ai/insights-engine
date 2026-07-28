from django.core.management.base import BaseCommand

from ...base_app import EventDrivenAPP


class Command(BaseCommand):
    """
    RabbitMQ consumers (EDA_* settings / Insights backend).

    Amazon MQ should use ``edaconsume_amq``.
    """

    def handle(self, *args, **options):
        EventDrivenAPP().backend.start_consuming()
