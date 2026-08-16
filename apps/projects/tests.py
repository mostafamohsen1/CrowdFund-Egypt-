from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.projects.models import Category, Project, Donation

User = get_user_model()


class ProjectLogicTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='creator@example.com',
            password='Password123!',
            first_name='Creator',
            last_name='User',
            phone_number='01012345678'
        )
        self.category = Category.objects.create(name='Tech Test')
        self.now = timezone.now()
        self.project = Project.objects.create(
            title='Test Project',
            details='Description of test project',
            category=self.category,
            total_target=Decimal('100000.00'),
            current_donations=Decimal('10000.00'), # 10% raised (< 25%)
            start_time=self.now - timedelta(days=1),
            end_time=self.now + timedelta(days=10),
            creator=self.user
        )

    def test_percentage_raised_and_cancellation_logic(self):
        self.assertEqual(self.project.percentage_raised, 10.0)
        self.assertTrue(self.project.can_be_cancelled)

        # Update donations to exceed 25%
        self.project.current_donations = Decimal('30000.00') # 30%
        self.project.save()

        self.assertEqual(self.project.percentage_raised, 30.0)
        self.assertFalse(self.project.can_be_cancelled)

    def test_donation_creation(self):
        donation = Donation.objects.create(
            project=self.project,
            user=self.user,
            amount=Decimal('5000.00')
        )
        self.assertEqual(donation.amount, Decimal('5000.00'))
        self.assertEqual(donation.project.title, 'Test Project')
