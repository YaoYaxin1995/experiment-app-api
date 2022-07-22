"""
Tests for the tags API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Experiment,
)

from experiment.serializers import TagSerializer


TAGS_URL = reverse('experiment:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail."""
    return reverse('experiment:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='password123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API request."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated API request."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name="Fmri")
        Tag.objects.create(user=self.user, name="EEG")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='behavior')
        tag = Tag.objects.create(user=self.user, name='pschology')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        tag = Tag.objects.create(user=self.user, name='memory')

        payload = {'name': 'emotion'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name='Mathmetics')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assighed_to_experiment(self):
        """Test listing tags by those assigned to experiments."""
        tag1 = Tag.objects.create(user=self.user, name='Tag test filter 1')
        tag2 = Tag.objects.create(user=self.user, name='Tag test filter 2')
        experiment = Experiment.objects.create(
            title='tag iCAN',
            time_minutes=5,
            price=Decimal('20'),
            user=self.user,
        )
        experiment.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""
        tag = Tag.objects.create(user=self.user, name='Eggs')
        Tag.objects.create(user=self.user, name='Lentils')
        experiment1 = Experiment.objects.create(
            title='Eggs Benedict tag test',
            time_minutes=60,
            price=Decimal('100'),
            user=self.user,
        )
        experiment2 = Experiment.objects.create(
            title='Herb Eggs tag test',
            time_minutes=20,
            price=Decimal('88'),
            user=self.user
        )
        experiment1.tags.add(tag)
        experiment2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
