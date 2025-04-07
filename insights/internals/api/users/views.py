from rest_framework import views, status
from rest_framework.request import Request
from rest_framework.response import Response

from insights.authentication.permissions import InternalAuthenticationPermission
from insights.users.models import User

from .serializers import ChangeUserLanguageSerializer


class ChangeUserLanguageView(views.APIView):
    serializer_class = ChangeUserLanguageSerializer
    queryset = User.objects.all()
    permission_classes = [InternalAuthenticationPermission]

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
