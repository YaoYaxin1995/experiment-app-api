"""
URL mapping for the experiment app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from experiment import views


router = DefaultRouter()
router.register('experiments', views.ExperimentViewSet)
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)

app_name = 'experiment'

urlpatterns = [
    path('', include(router.urls)),
]
