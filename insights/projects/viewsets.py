from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.projects.models import Project
from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source


class ProjectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [ProjectAuthPermission]
    queryset = Project.objects.all()

    @action(
        detail=True, methods=["get"], url_path="sources/(?P<source_slug>[^/.]+)/search"
    )
    def retrieve_source_data(self, request, source_slug=None, *args, **kwargs):
        SourceQuery = get_source(slug=source_slug)
        query_kwargs = {}
        if SourceQuery is None:
            return Response(
                {"detail": f"could not find a source with the slug {source_slug}"},
                status.HTTP_404_NOT_FOUND,
            )
        filters = (request.data or request.query_params or {}).copy()
        operation = filters.pop("operation", "list")

        tags = filters.pop("tags", None)
        if tags:
            filters["tags"] = tags.split(",")
        field_name = filters.pop("field_name", None)
        if field_name:
            query_kwargs["field_name"] = field_name

        serialized_source = SourceQuery.execute(
            filters=filters,
            operation=operation,
            parser=parse_dict_to_json,
            project=self.get_object(),
            user_email=self.request.user.email,
            return_format="select_input",
            query_kwargs=query_kwargs,
        )
        return Response(serialized_source, status.HTTP_200_OK)
