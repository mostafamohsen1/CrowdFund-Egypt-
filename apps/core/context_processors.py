from apps.projects.models import Category, Tag

def global_categories(request):
    """
    Context processor to pass categories and popular tags to all templates.
    """
    return {
        'nav_categories': Category.objects.all()[:8],
        'nav_tags': Tag.objects.all()[:10],
    }
