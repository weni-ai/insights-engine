from django.utils.module_loading import import_string
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.projects.parsers import parse_dict_to_json


class ProjectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [ProjectAuthPermission]

    def get_source(self, slug: str):
        try:
            source_path = (
                f"insights.sources.{slug}.usecases.query_execute.QueryExecutor"
            )
            return import_string(source_path)
        except (ModuleNotFoundError, ImportError, AttributeError) as e:
            print(f"Error: {e}")
            return None

    @action(
        detail=True, methods=["get"], url_path="sources/(?P<source_slug>[^/.]+)/data"
    )
    def retrieve_source_data(self, request, source_slug=None, *args, **kwargs):
        SourceQuery = self.get_source(slug=source_slug)
        if SourceQuery is None:
            return Response(
                {"detail": f"could not find a source with the slug {source_slug}"},
                status.HTTP_404_NOT_FOUND,
            )
        filters = request.data or request.query_params or {}
        action = filters.pop("action", "list")

        tags = filters.pop("tags", None)
        if tags:
            filters["tags"] = tags.split(",")

        serialized_source = SourceQuery.execute(
            filters=filters,
            action=action,
            parser=parse_dict_to_json,
            project=self.get_object(),
            user_email=self.request.user.email,
            return_format="select_input",
        )
        return Response(serialized_source, status.HTTP_200_OK)
