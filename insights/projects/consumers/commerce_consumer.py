import amqp
from insights.event_driven.consumers import EDAConsumer
from insights.event_driven.parsers.json_parser import JSONParser
from insights.projects.models import Project
from insights.projects.usecases.enable_custom_dashboard import enable_custom_dashboard

class ProjectCommerceConsumer(EDAConsumer):
    @staticmethod
    def consume(message: amqp.Message):
        channel = message.channel
        print(f"[ProjectCommerceConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            project_id = body.get('uuid')
            if not project_id:
                print("[ProjectCommerceConsumer] - Missing project_id in message")
                channel.basic_reject(message.delivery_tag, requeue=False)
                return
                
            project = Project.objects.filter(pk=project_id).first()
            if not project:
                print(f"[ProjectCommerceConsumer] - Project with id {project_id} not found")
                channel.basic_reject(message.delivery_tag, requeue=False)
                return
            
            enable_custom_dashboard(project)

            channel.basic_ack(message.delivery_tag)
        except Exception as exception:
            channel.basic_reject(message.delivery_tag, requeue=False)
            print(f"[ProjectConsumer] - Message rejected by: {exception}")