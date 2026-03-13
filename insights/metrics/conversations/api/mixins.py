from insights.metrics.conversations.resolvers import ConversationsMetricsServiceResolver
from insights.metrics.conversations.services import BaseConversationsMetricsService


class ConversationsMetricsServiceResolverMixin:
    """
    Mixin to get the correct service for the conversations metrics endpoints
    """

    _resolver = None
    _service = None

    @property
    def resolver(self) -> ConversationsMetricsServiceResolver:
        if self._resolver is None:
            self._resolver = ConversationsMetricsServiceResolver()

        return self._resolver

    @property
    def service(self) -> BaseConversationsMetricsService:
        if self._service is None:
            query_params = self.request.query_params
            project_uuid = query_params.get("project_uuid")

            try:
                action = getattr(self, self.action)
                force_use_real_service = getattr(
                    action, "force_use_real_service", False
                )
            except AttributeError:
                force_use_real_service = False

            self._service = self.resolver.resolve(
                request=self.request,
                project_uuid=project_uuid,
                force_use_real_service=force_use_real_service,
            )

        return self._service
