"""
Serializers for experiment API.
"""
from rest_framework import serializers

from core.models import (
    Experiment,
    Tag,
    Ingredient,
)


class IngredientSerializer(serializers.ModelSerializer):
    """Serialize for ingredient."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class ExperimentSerializer(serializers.ModelSerializer):
    """Serializer for Experiments."""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Experiment
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link', 'tags',
            'ingredients',
        ]
        read_only_field = ['id']


class ExperimentDetailSerializer(ExperimentSerializer):
    """Serializer for experiment detail view."""

    class Meta(ExperimentSerializer.Meta):
        fields = ExperimentSerializer.Meta.fields + ['description']

    def _get_or_create_tags(self, tags, experiment):
        """Handle getting or creating tags on as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            experiment.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, experiment):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, create = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient,
            )
            experiment.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """Create a experiment."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        experiment = Experiment.objects.create(**validated_data)
        self._get_or_create_tags(tags, experiment)
        self._get_or_create_ingredients(ingredients, experiment)
        return experiment

    def update(self, instance, validated_data):
        """Update experimrnt."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
