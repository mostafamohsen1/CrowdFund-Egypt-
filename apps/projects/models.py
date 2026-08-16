from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-folder', help_text='Bootstrap icon class name (e.g. bi-heart-pulse)')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    details = models.TextField(help_text="Detailed description of the campaign and its fundraising goal")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='projects')
    cover_image = models.ImageField(upload_to='projects/covers/')
    total_target = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('10.00'))],
        help_text="Target amount to raise in EGP"
    )
    current_donations = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tags = models.ManyToManyField(Tag, related_name='projects', blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    
    is_featured = models.BooleanField(default=False, help_text="Admin selected featured project for homepage")
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def percentage_raised(self):
        if not self.total_target or self.total_target == 0:
            return 0
        pct = (self.current_donations / self.total_target) * Decimal('100')
        return min(round(float(pct), 1), 100)

    @property
    def is_running(self):
        now = timezone.now()
        return not self.is_cancelled and self.start_time <= now <= self.end_time

    @property
    def days_left(self):
        now = timezone.now()
        if now >= self.end_time:
            return 0
        diff = self.end_time - now
        return diff.days

    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings.exists():
            return 0.0
        avg = ratings.aggregate(models.Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    @property
    def can_be_cancelled(self):
        """
        Project creator can cancel the project if donations are less than 25% of the target.
        """
        if self.is_cancelled:
            return False
        if not self.total_target:
            return True
        threshold = self.total_target * Decimal('0.25')
        return self.current_donations < threshold


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.project.title}"


class Donation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='donations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    donated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donated_at']

    def __str__(self):
        return f"{self.user.get_full_name()} donated {self.amount} EGP to {self.project.title}"


class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.project.title}"


class Rating(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.rating} Stars by {self.user.email} for {self.project.title}"


class Report(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = f"Project: {self.project.title}" if self.project else f"Comment ID #{self.comment_id}"
        return f"Report by {self.reporter.email} on {target}"
