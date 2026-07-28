import os
import signal

from weni.eda.django.eda_app.management.commands.edaconsume import (
    Command as WeniEDACommand,
)


def handle_sigterm(*args):
    """
    Handle SIGTERM signal - exit gracefully.
    """
    print("[msg_edaconsume] - Received SIGTERM signal, exiting gracefully")
    os._exit(0)


class Command(WeniEDACommand):
    """
    RabbitMQ consumers (EDA_* / ConnectionParamsFactory).

    Amazon MQ should use ``edaconsume_amq`` or pass
    ``--params-class weni.eda.django.AMQConnectionParamsFactory``.
    """

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, handle_sigterm)
        super().handle(*args, **options)
