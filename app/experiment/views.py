"""
Views for experiment APIs.
"""
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Experiment,
    Tag,
    Ingredient,
)

from experiment import serializers


class ExperimentViewSet(viewsets.ModelViewSet):
    """View for manage experiment APIs."""
    serializer_class = serializers.ExperimentDetailSerializer
    queryset = Experiment.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve experiments for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.ExperimentSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new experiment."""
        serializer.save(user=self.request.user)


class BaseExperimentAttrViewSet(mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin,
                                mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    """Base viewset for experiment attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter querset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')



class TagViewSet(BaseExperimentAttrViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseExperimentAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
