from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .validators import validate_egyptian_phone

User = get_user_model()


class AccountsModelAndValidatorTest(TestCase):

    def test_valid_egyptian_phone(self):
        valid_numbers = ['01012345678', '01198765432', '01234567890', '01511112222', '+201012345678']
        for number in valid_numbers:
            try:
                validate_egyptian_phone(number)
            except ValidationError:
                self.fail(f"validate_egyptian_phone raised ValidationError unexpectedly for {number}")

    def test_invalid_egyptian_phone(self):
        invalid_numbers = ['12345', '01312345678', '01012345', '+101012345678', 'abcdefghijk']
        for number in invalid_numbers:
            with self.assertRaises(ValidationError):
                validate_egyptian_phone(number)

    def test_user_creation_and_token_validity(self):
        user = User.objects.create_user(
            email='testuser@example.com',
            password='Password123!',
            first_name='Test',
            last_name='User',
            phone_number='01012345678'
        )
        self.assertTrue(user.is_token_valid())
        self.assertFalse(user.is_email_verified)
        self.assertEqual(user.email, 'testuser@example.com')
