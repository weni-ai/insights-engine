from abc import ABC, abstractmethod

import amqp
from sentry_sdk import capture_exception

from insights.event_driven.backends.pyamqp_backend import basic_publish

from .signals import message_finished, message_started


def pyamqp_call_dlx_when_error(
    routing_key: str, default_exchange: str, consumer_name: str
):
    def decorator(consumer):
        def consumer_wrapper(*args, **kw):
            message = args[0]
            channel = message.channel
            try:
                return consumer(*args, **kw)
            except Exception as err:
                capture_exception(err)
                channel.basic_reject(message.delivery_tag, requeue=False)
                print(f"[{consumer_name}] - Message rejected by: {err}")
                callback_body = {
                    "original_message": message.body.decode("utf-8"),
                    "error_type": str(type(err)),
                    "error_message": str(err),
                }
                exchange = message.headers.get("callback_exchange") or default_exchange
                basic_publish(
                    channel=channel,
                    content=callback_body,
                    properties={"delivery_mode": 2},
                    exchange=exchange,
                )

        return consumer_wrapper

    return decorator


class EDAConsumer(ABC):  # pragma: no cover
    def handle(self, message: amqp.Message):
        message_started.send(sender=self)
        try:
            self.consume(message)
        finally:
            message_finished.send(sender=self)

    @abstractmethod
    def consume(self, message: amqp.Message):
        pass
