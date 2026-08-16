import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.projects.models import Project, Category, Tag
from apps.core.services.ai_service import build_crowdfund_context, generate_chat_response

User = get_user_model()


class AIChatbotTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='Password123!',
            first_name='Kareem',
            last_name='Nabil',
            phone_number='01099887766',
            is_active=True,
            is_email_verified=True
        )

        self.category = Category.objects.create(
            name='Environment & Clean Tech',
            slug='environment-clean-tech',
            description='Renewable energy and eco initiatives in Egypt'
        )

        self.tag = Tag.objects.create(name='solar')

        now = timezone.now()
        self.project = Project.objects.create(
            title='Cairo Solar Green Roofs Initiative',
            details='Transforming urban rooftops into solar power generators and green community gardens across Cairo.',
            category=self.category,
            total_target=Decimal('250000.00'),
            current_donations=Decimal('85000.00'),
            start_time=now - timedelta(days=5),
            end_time=now + timedelta(days=25),
            creator=self.user,
            is_featured=True,
            cover_image='projects/covers/sample.jpg'
        )
        self.project.tags.add(self.tag)

    def test_build_crowdfund_context(self):
        """Test that the live database context is properly assembled with campaigns and categories."""
        system_instruction, meta = build_crowdfund_context()
        self.assertIn('Cairo Solar Green Roofs Initiative', system_instruction)
        self.assertIn('Environment & Clean Tech', system_instruction)
        self.assertIn('250,000.00 EGP', system_instruction)
        self.assertIn('/projects/cairo-solar-green-roofs-initiative/', system_instruction)
        self.assertEqual(meta['total_count'], 1)

    def test_chat_api_get_not_allowed(self):
        """GET request to /api/chat/ should return 405 Method Not Allowed."""
        response = self.client.get(reverse('chat_api'))
        self.assertEqual(response.status_code, 405)

    def test_chat_api_empty_message(self):
        """Sending empty message should return 400 status."""
        response = self.client.post(
            reverse('chat_api'),
            data=json.dumps({'message': '   '}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')

    def test_chat_api_success_with_recommendation(self):
        """Posting a recommendation query should return 200 with relevant campaign content."""
        response = self.client.post(
            reverse('chat_api'),
            data=json.dumps({'message': 'Can you recommend solar or green projects?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('response', data)
        self.assertTrue(len(data['response']) > 10)

    def test_chat_api_multi_turn_history(self):
        """Posting with conversation history should properly process the multi-turn context."""
        payload = {
            'message': 'Which category does it belong to?',
            'history': [
                {'role': 'user', 'content': 'Tell me about the Cairo Solar project.'},
                {'role': 'assistant', 'content': 'Cairo Solar Green Roofs Initiative is an environment campaign.'}
            ]
        }
        response = self.client.post(
            reverse('chat_api'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('response', data)

    def test_smart_fallback_policy_inquiry(self):
        """Inquiring about cancellation policy returns accurate platform policy (<25% threshold)."""
        response_text = generate_chat_response("What is the project cancellation policy?")
        self.assertIn("25%", response_text)
        self.assertIn("cancellation", response_text.lower())
