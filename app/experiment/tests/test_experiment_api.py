"""
Test for experiment APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Experiment,
    Tag,
    Ingredient,
)

from experiment.serializers import (
    ExperimentSerializer,
    ExperimentDetailSerializer,
    )


EXPERIMENT_URL = reverse('experiment:experiment-list')


def detail_url(experiment_id):
    """Create and return a experiment URL."""
    return reverse('experiment:experiment-detail', args=[experiment_id])


def create_experiment(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample experiment title',
        'time_minutes': 22,
        'price': Decimal("5.22"),
        'description': 'Sample description',
        'link': 'http:example.com/experiment.pdf',
    }
    defaults.update(params)

    experiment = Experiment.objects.create(user=user, **defaults)
    return experiment

def create_user(**params):
    """create and return a new user."""
    return get_user_model().objects.create(**params)

class PublicExperimentAPITest(TestCase):
    """Test unauthenticated API request."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_requuired(self):
        """Test auth is required to call API."""

        res = self.client.get(EXPERIMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateExperimentApiTest(TestCase):
    """Test authenticated API request."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@example.com', password='testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_experiment(self):
        """Test retrieve a list of experiment."""
        create_experiment(self.user)
        create_experiment(self.user)

        res = self.client.get(EXPERIMENT_URL)

        experiments = Experiment.objects.all().order_by('-id')
        serializer = ExperimentSerializer(experiments, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_experiment_list_limited_to_user(self):
        """Test list of experiments is limited to authenticated user."""
        other_user = create_user(email='other_user@example.com',password='otherpass123')

        create_experiment(self.user)
        create_experiment(other_user)

        res = self.client.get(EXPERIMENT_URL)

        experiments = Experiment.objects.filter(user=self.user)
        serializer = ExperimentSerializer(experiments, many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_experiment_detail(self):
        """Test get experiment detail."""
        experiment = create_experiment(user=self.user)

        url = detail_url(experiment.id)
        res = self.client.get(url)

        serializer = ExperimentDetailSerializer(experiment)
        self.assertEqual(res.data, serializer.data)

    def test_create_experiment(self):
        """Test creating a experiment."""
        payload = {
            'title': 'Sample experiment',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }

        res = self.client.post(EXPERIMENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        experiment = Experiment.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(experiment, k), v)
        self.assertEqual(experiment.user, self.user)

    def test_partial_update(self):
        """Test partial update of a experiment."""
        original_link = 'http://example.com/experiment.pdf'
        experiment = create_experiment(
            user=self.user,
            title='Sample experiment title',
            link=original_link,
        )

        payload = {'title': 'New experiment title'}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload)

        self .assertEqual(res.status_code, status.HTTP_200_OK)
        experiment.refresh_from_db()
        self.assertEqual(experiment.title, payload['title'])
        self.assertEqual(experiment.link, original_link)
        self.assertEqual(experiment.user, self.user)

    def test_full_update(self):
        """Test full update of a experiment."""
        experiment = create_experiment(
            user=self.user,
            title='Sample experiment title',
            link='http://example.com/experiment.pdf',
            description = 'sample experiment description.'
        )

        payload = {
            'title': 'New title',
            'link': 'http://example.com/new-experiment.pdf',
            'description': 'New experiment description',
            'time_minutes': 10,
            'price': Decimal('5.33')
        }
        url = detail_url(experiment.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        experiment.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(experiment, k), v)
        self.assertEqual(experiment.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the experiment user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        experiment = create_experiment(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(experiment.id)
        self.client.patch(url, payload)

        experiment.refresh_from_db()
        self.assertEqual(experiment.user, self.user)

    def test_delete_experiment(self):
        """Test deleting a experiment successful."""
        experiment = create_experiment(user=self.user)

        url = detail_url(experiment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Experiment.objects.filter(id=experiment.id).exists())

    def test_delete_other_users_experiment_error(self):
        """Test tring to delete another users experiment gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        experiment = create_experiment(user=new_user)

        url = detail_url(experiment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Experiment.objects.filter(id=experiment.id).exists())

    def test_create_experiment_with_new_tag(self):
        """Test creating a experiment with new tags."""
        payload = {
            'title': 'Emotion Experiemnt',
            'time_minutes': 30,
            'price': Decimal('30'),
            'tags': [{'name': 'female'}, {'name': 'sleep'}],
        }
        res = self.client.post(EXPERIMENT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        experiments = Experiment.objects.filter(user=self.user)
        self.assertEqual(experiments.count(),1)
        experiment = experiments[0]
        self.assertEqual(experiment.tags.count(), 2)
        for tag in payload['tags']:
            exists = experiment.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_experiment_with_existing_tags(self):
        """Test create a experiment with existing tag."""
        tag_BNU = Tag.objects.create(user=self.user, name='BNU')
        payload = {
            'title': 'Math trainning',
            'time_minutes': 60,
            'price': Decimal('200'),
            'tags': [{'name': 'BNU'}, {'name': 'trainning'}],
        }
        res = self.client.post(EXPERIMENT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        experiments = Experiment.objects.filter(user=self.user)
        self.assertEqual(experiments.count(), 1)
        experiment = experiments[0]
        self.assertEqual(experiment.tags.count(), 2)
        self.assertIn(tag_BNU, experiment.tags.all())
        for tag in payload['tags']:
            exists = experiment.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a experiment."""
        experiment = create_experiment(user=self.user)

        payload = {'tags': [{'name': 'Morning'}]}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Morning')
        self.assertIn(new_tag, experiment.tags.all())

    def test_update_experiment_assign_tag(self):
        """Test assigning an existing tag when updating a experiment."""
        tag_night = Tag.objects.create(user=self.user, name='Night')
        experiment = create_experiment(user=self.user)
        experiment.tags.add(tag_night)

        tag_afternoon = Tag.objects.create(user=self.user, name='Afternoon')
        payload = {'tags': [{'name': 'Afternoon'}]}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_afternoon, experiment.tags.all())
        self.assertNotIn(tag_night, experiment.tags.all())


    def test_clear_experiment_tags(self):
        """Test clearing a experiment tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        experiment = create_experiment(user=self.user)
        experiment.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(experiment.tags.count(), 0)

    def test_experiment_with_new_ingredients(self):
        """Test creating a experiment with new ingredients."""
        payload = {
            'title': 'Emotion Trainning',
            'time_minutes': 60,
            'price': Decimal('25'),
            'ingredients': [{'name': 'college'}, {'name': 'right hand'}],
        }
        res = self.client.post(EXPERIMENT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        experiments = Experiment.objects.filter(user=self.user)
        self.assertEqual(experiments.count(), 1)
        experiment = experiments[0]
        self.assertEqual(experiment.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = experiment.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_experiment_with_existing_ingredient(self):
        """Test creating a new experiment with existing ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Middle school student')
        payload = {
            'title': 'student math trainning',
            'time_minutes': 50,
            'price': Decimal('40.0'),
            'ingredients': [{'name': 'Middle school student'}, {'name': 'dyscalculia'}],
        }
        res =self.client.post(EXPERIMENT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        experiments = Experiment.objects.filter(user=self.user)
        self.assertEqual(experiments.count(), 1)
        experiment=experiments[0]
        self.assertEqual(experiment.ingredients.count(), 2)
        self.assertIn(ingredient, experiment.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = experiment.ingredients.filter(
                name=ingredient['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a experiment."""
        experiment = create_experiment(user=self.user)

        payload = {'ingredients': [{'name': 'ingredient1'}]}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='ingredient1')
        self.assertIn(new_ingredient, experiment.ingredients.all())

    def test_update_experiment_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a experiment."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='ingredient1')
        experiment = create_experiment(user=self.user)
        experiment.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='ingredient2')
        payload = {'ingredients': [{'name': 'ingredient2'}]}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, experiment.ingredients.all())
        self.assertNotIn(ingredient1, experiment.ingredients.all())

    def test_clear_experiment_ingredients(self):
        """Test clearing a experiments ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name='clearIngredient')
        experiment = create_experiment(user=self.user)
        experiment.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(experiment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(experiment.ingredients.count(), 0)







