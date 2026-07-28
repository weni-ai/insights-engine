import os
import signal

from django.conf import settings
from weni.eda.django.eda_app.management.commands.edaconsume import (
    Command as WeniEDACommand,
)


AMQ_HANDLE = "insights.event_driven.handle_amq.handle_amq_consumers"
AMQ_PARAMS_CLASS = "weni.eda.django.AMQConnectionParamsFactory"
AMQ_BACKEND = "weni.eda.backends.pyamqp_backend.PyAMQPConnectionBackend"


def handle_sigterm(*args):
    """
    Handle SIGTERM signal - exit gracefully.
    """
    print("[edaconsume_amq] - Received SIGTERM signal, exiting gracefully")
    os._exit(0)


class Command(WeniEDACommand):
    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, handle_sigterm)
        options["handle"] = options.get("handle") or AMQ_HANDLE
        options["params_class"] = AMQ_PARAMS_CLASS
        options["backend"] = options.get("backend") or AMQ_BACKEND

        print(
            "[edaconsume_amq] Connecting to Amazon MQ "
            f"host={settings.AMQ_BROKER_HOST} port={settings.AMQ_BROKER_PORT} "
            f"vhost={settings.AMQ_VIRTUAL_HOST} "
            f"queue={settings.PROJECT_AMQ_QUEUE_NAME}"
        )
        super().handle(*args, **options)
