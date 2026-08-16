from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
from datetime import timedelta
from .validators import validate_egyptian_phone


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email address must be provided'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone_number = models.CharField(
        _('mobile phone'),
        max_length=20,
        validators=[validate_egyptian_phone],
        help_text=_('Must be a valid Egyptian mobile number (e.g. 01012345678 or +201123456789)')
    )
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='avatars/',
        default='avatars/default-avatar.png',
        blank=True
    )
    
    # Email Activation Fields
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    token_created_at = models.DateTimeField(default=timezone.now)

    # Optional Profile Attributes
    birthdate = models.DateField(_('birthdate'), null=True, blank=True)
    facebook_profile = models.URLField(_('facebook profile URL'), max_length=300, blank=True)
    country = models.CharField(_('country'), max_length=100, blank=True, default='Egypt')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def is_token_valid(self):
        """
        Token is valid for 24 hours (1440 minutes) from generation.
        """
        if not self.token_created_at:
            return False
        expiration_time = self.token_created_at + timedelta(hours=24)
        return timezone.now() <= expiration_time

    def generate_new_token(self):
        self.verification_token = uuid.uuid4()
        self.token_created_at = timezone.now()
        self.save(update_fields=['verification_token', 'token_created_at'])
