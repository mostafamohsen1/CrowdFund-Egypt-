from django.shortcuts import render
from django.db.models import Q, Avg, Count
from django.utils import timezone
from apps.projects.models import Project, Category, Tag


def home_view(request):
    now = timezone.now()

    # Search Query logic
    query = request.GET.get('q', '').strip()
    if query:
        search_results = Project.objects.filter(
            Q(title__icontains=query) | Q(tags__name__icontains=query) | Q(details__icontains=query),
            is_cancelled=False
        ).distinct().select_related('category', 'creator')
        
        return render(request, 'core/search_results.html', {
            'query': query,
            'projects': search_results,
        })

    # 1. Slider: Highest five rated running projects
    slider_projects = Project.objects.filter(
        is_cancelled=False,
        start_time__lte=now,
        end_time__gte=now
    ).annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating', '-current_donations')[:5]

    # 2. Latest 5 projects
    latest_projects = Project.objects.filter(
        is_cancelled=False
    ).select_related('category', 'creator').order_by('-created_at')[:5]

    # 3. Featured 5 projects (selected by admin)
    featured_projects = Project.objects.filter(
        is_featured=True,
        is_cancelled=False
    ).select_related('category', 'creator').order_by('-created_at')[:5]

    # 4. List of Categories with project counts
    categories = Category.objects.annotate(project_count=Count('projects')).all()

    context = {
        'slider_projects': slider_projects,
        'latest_projects': latest_projects,
        'featured_projects': featured_projects,
        'categories': categories,
    }
    return render(request, 'core/home.html', context)


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500_view(request):
    return render(request, '500.html', status=500)


import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .services.ai_service import generate_chat_response


@require_POST
def chat_api_view(request):
    """
    Dedicated REST API endpoint for the AI Chatbot.
    Accepts: JSON { "message": "...", "history": [...] }
    Returns: JSON { "status": "success", "response": "..." }
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        user_message = data.get('message', '').strip()
        history = data.get('history', [])

        if not user_message:
            return JsonResponse({
                'status': 'error',
                'error': 'Message content cannot be empty.'
            }, status=400)

        # Generate contextualized AI response
        ai_response = generate_chat_response(user_message, conversation_history=history)

        return JsonResponse({
            'status': 'success',
            'response': ai_response
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'error': 'Invalid JSON format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': 'Sorry, the AI assistant is temporarily unavailable. Please try again.'
        }, status=500)
