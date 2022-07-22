"""
Test for the ingredients API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Experiment,
)

from experiment.serializers import IngredientSerializer


INGREDIENT_URL = reverse('experiment:ingredient-list')


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse('experiment:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='testpass123'):
    """Craete and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API request."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name='freshman')
        Ingredient.objects.create(user=self.user, name='right hand')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limits_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        user2 = create_user(email='user2@exmaple.com')
        Ingredient.objects.create(user=user2, name='sophomore')
        ingredient = Ingredient.objects.create(user=self.user, name='junior')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='college students'
            )

        payload = {'name': 'high school students'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='deleted ingredient'
            )

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assighed_to_experiment(self):
        """Test listing ingredients by those assigned to experiments."""
        in1 = Ingredient.objects.create(
            user=self.user,
            name='ingredient test filter 1'
            )
        in2 = Ingredient.objects.create(
            user=self.user,
            name='ingredient test filter 2'
            )
        experiment = Experiment.objects.create(
            title='iCAN',
            time_minutes=5,
            price=Decimal('20'),
            user=self.user,
        )
        experiment.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL,  {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""
        ing = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Lentils')
        experiment1 = Experiment.objects.create(
            title='Eggs Benedict',
            time_minutes=60,
            price=Decimal('100'),
            user=self.user,
        )
        experiment2 = Experiment.objects.create(
            title='Herb Eggs',
            time_minutes=20,
            price=Decimal('88'),
            user=self.user
        )
        experiment1.ingredients.add(ing)
        experiment2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
