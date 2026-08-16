from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile

from apps.projects.models import Category, Tag, Project, ProjectImage, Donation, Comment, Rating

User = get_user_model()


def generate_sample_cover(title, bg_color='#4f46e5'):
    img = Image.new('RGB', (800, 480), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Simple aesthetic pattern
    draw.rectangle([40, 40, 760, 440], outline='#ffffff', width=3)
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    return ContentFile(buffer.getvalue(), name=f"{title.lower().replace(' ', '_')}.jpg")


class Command(BaseCommand):
    help = 'Seeds initial categories, superuser, tags, and realistic demo campaigns.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database with demo data..."))

        # 1. Superuser & Demo User
        admin_user, created = User.objects.get_or_create(
            email='mostafa@gmail.com',
            defaults={
                'first_name': 'Mostafa',
                'last_name': 'Admin',
                'phone_number': '01012345678',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_email_verified': True,
                'country': 'Egypt'
            }
        )
        if created:
            admin_user.set_password('mostafa1234')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Superuser created: mostafa@gmail.com / mostafa1234"))

        demo_user, _ = User.objects.get_or_create(
            email='ahmed.hassan@example.com',
            defaults={
                'first_name': 'Ahmed',
                'last_name': 'Hassan',
                'phone_number': '01198765432',
                'is_active': True,
                'is_email_verified': True,
                'country': 'Egypt'
            }
        )
        demo_user.set_password('password123')
        demo_user.save()

        # 2. Categories
        categories_data = [
            ('Technology', 'bi-cpu', 'Innovations in AI, robotics, mobile applications, and hardtech in Egypt.'),
            ('Charity & Social', 'bi-heart-pulse', 'Community outreach, food banks, and shelter support programs.'),
            ('Education', 'bi-book', 'Scholarships, school renovations, and digital literacy initiatives.'),
            ('Medical & Health', 'bi-hospital', 'Medical treatments, equipment funding, and clinic development.'),
            ('Creative & Arts', 'bi-palette', 'Film production, music recording, publishing, and cultural heritage.'),
            ('Environment', 'bi-tree', 'Solar energy projects, recycling drives, and green urban spaces in Cairo.')
        ]

        created_categories = {}
        for name, icon, desc in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'description': desc}
            )
            created_categories[name] = cat

        # 3. Tags
        tags_data = ['cairo', 'alexandria', 'tech', 'health', 'education', 'social', 'green', 'youth']
        created_tags = {}
        for tname in tags_data:
            tg, _ = Tag.objects.get_or_create(name=tname)
            created_tags[tname] = tg

        # 4. Demo Projects
        now = timezone.now()

        projects_def = [
            {
                'title': 'Solar Powered Water Pumps for Rural Upper Egypt',
                'category': created_categories['Environment'],
                'total_target': Decimal('350000.00'),
                'current_donations': Decimal('210000.00'),
                'details': 'Providing sustainable solar water pumping infrastructure to farming communities in Upper Egypt to increase agricultural yield and clean water access.',
                'is_featured': True,
                'tags': [created_tags['green'], created_tags['cairo'], created_tags['social']],
                'bg': '#059669',
            },
            {
                'title': 'Cairo Youth Robotics & AI Learning Hub',
                'category': created_categories['Technology'],
                'total_target': Decimal('180000.00'),
                'current_donations': Decimal('95000.00'),
                'details': 'Building a state-of-the-art free robotics lab in Nasr City to train underprivileged high school students in modern AI programming and hardware engineering.',
                'is_featured': True,
                'tags': [created_tags['tech'], created_tags['youth'], created_tags['education']],
                'bg': '#4f46e5',
            },
            {
                'title': 'Alexandria Coastal Beach Cleanup & Coral Preservation',
                'category': created_categories['Environment'],
                'total_target': Decimal('75000.00'),
                'current_donations': Decimal('52000.00'),
                'details': 'Organizing weekly volunteer cleanup campaigns and marine habitat protection efforts along Alexandria coastline.',
                'is_featured': True,
                'tags': [created_tags['alexandria'], created_tags['green']],
                'bg': '#06b6d4',
            },
            {
                'title': 'Childrens Hospital Emergency Unit Renovation',
                'category': created_categories['Medical & Health'],
                'total_target': Decimal('500000.00'),
                'current_donations': Decimal('340000.00'),
                'details': 'Upgrading ICU ventilation units and monitoring systems at pediatric care facilities to serve low-income families.',
                'is_featured': True,
                'tags': [created_tags['health'], created_tags['social']],
                'bg': '#e11d48',
            },
            {
                'title': 'Mobile Digital Library Bus for Villages',
                'category': created_categories['Education'],
                'total_target': Decimal('120000.00'),
                'current_donations': Decimal('45000.00'),
                'details': 'Converting a vintage bus into a mobile library equipped with tablets, internet access, and thousands of books for children in rural governorates.',
                'is_featured': True,
                'tags': [created_tags['education'], created_tags['youth']],
                'bg': '#d97706',
            },
            {
                'title': 'Egyptian Artisan Pottery & Craft Revival',
                'category': created_categories['Creative & Arts'],
                'total_target': Decimal('90000.00'),
                'current_donations': Decimal('15000.00'),
                'details': 'Supporting traditional master potters in Fayoum with modern electric kilns and online marketing training to preserve heritage crafts.',
                'is_featured': False,
                'tags': [created_tags['cairo'], created_tags['social']],
                'bg': '#7c3aed',
            }
        ]

        for pdata in projects_def:
            p, pcreated = Project.objects.get_or_create(
                title=pdata['title'],
                defaults={
                    'category': pdata['category'],
                    'details': pdata['details'],
                    'total_target': pdata['total_target'],
                    'current_donations': pdata['current_donations'],
                    'start_time': now - timedelta(days=5),
                    'end_time': now + timedelta(days=25),
                    'creator': admin_user,
                    'is_featured': pdata['is_featured'],
                }
            )
            if pcreated:
                p.cover_image.save(f"cover_{p.id}.jpg", generate_sample_cover(p.title, pdata['bg']))
                p.tags.set(pdata['tags'])
                p.save()

                # Add sample ratings
                Rating.objects.create(project=p, user=admin_user, rating=5)
                Rating.objects.create(project=p, user=demo_user, rating=4)

                # Add sample comments
                c1 = Comment.objects.create(
                    project=p,
                    user=demo_user,
                    content="This is an incredible initiative! Proud to see such projects in Egypt."
                )
                Comment.objects.create(
                    project=p,
                    user=admin_user,
                    parent=c1,
                    content="Thank you Ahmed for your support! We will post weekly progress updates."
                )

                # Add sample donation
                Donation.objects.create(
                    project=p,
                    user=demo_user,
                    amount=Decimal('500.00')
                )

        self.stdout.write(self.style.SUCCESS("Database successfully seeded with categories, projects, ratings, comments, and donations!"))
