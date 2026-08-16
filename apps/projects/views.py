from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .models import Project, Category, Tag, ProjectImage, Donation, Comment, Rating, Report
from .forms import (
    ProjectForm, ProjectGalleryImagesForm, DonationForm,
    CommentForm, RatingForm, ReportForm
)


def project_list_view(request):
    projects_list = Project.objects.filter(is_cancelled=False).select_related('category', 'creator').prefetch_related('tags')
    
    category_slug = request.GET.get('category')
    if category_slug:
        projects_list = projects_list.filter(category__slug=category_slug)

    sort_by = request.GET.get('sort', 'latest')
    if sort_by == 'target':
        projects_list = projects_list.order_by('-total_target')
    elif sort_by == 'popular':
        projects_list = projects_list.annotate(num_donations=Count('donations')).order_by('-num_donations')
    elif sort_by == 'ending':
        projects_list = projects_list.filter(end_time__gt=timezone.now()).order_by('end_time')
    else:
        projects_list = projects_list.order_by('-created_at')

    paginator = Paginator(projects_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'sort_by': sort_by,
    }
    return render(request, 'projects/project_list.html', context)


def category_projects_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    projects_list = Project.objects.filter(category=category, is_cancelled=False).select_related('creator')
    
    paginator = Paginator(projects_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'projects/category_projects.html', context)


def project_detail_view(request, slug):
    project = get_object_or_404(
        Project.objects.select_related('category', 'creator').prefetch_related('images', 'tags', 'comments__user', 'comments__replies__user'),
        slug=slug
    )

    donation_form = DonationForm()
    comment_form = CommentForm()
    report_form = ReportForm()

    # User's existing rating (if logged in)
    user_rating = None
    if request.user.is_authenticated:
        user_rating_obj = Rating.objects.filter(project=project, user=request.user).first()
        if user_rating_obj:
            user_rating = user_rating_obj.rating

    # Handle Forms Post
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, _("Please log in to participate or donate."))
            return redirect('login')

        action = request.POST.get('action_type')

        # 1. Donation Action
        if action == 'donate':
            donation_form = DonationForm(request.POST)
            if donation_form.is_valid():
                amount = donation_form.cleaned_data['amount']
                with transaction.atomic():
                    Donation.objects.create(
                        project=project,
                        user=request.user,
                        amount=amount
                    )
                    project.current_donations += amount
                    project.save(update_fields=['current_donations'])
                messages.success(request, _(f"Thank you! Your donation of {amount} EGP was received successfully."))
                return redirect('project_detail', slug=project.slug)

        # 2. Rating Action
        elif action == 'rate':
            score = request.POST.get('rating_score')
            if score and score.isdigit():
                score_int = int(score)
                if 1 <= score_int <= 5:
                    Rating.objects.update_or_create(
                        project=project,
                        user=request.user,
                        defaults={'rating': score_int}
                    )
                    messages.success(request, _("Thank you for rating this campaign!"))
                    return redirect('project_detail', slug=project.slug)

        # 3. Comment Action
        elif action == 'comment':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.project = project
                comment.user = request.user
                parent_id = request.POST.get('parent_id')
                if parent_id and parent_id.isdigit():
                    parent_comment = Comment.objects.filter(id=int(parent_id), project=project).first()
                    if parent_comment:
                        comment.parent = parent_comment
                comment.save()
                messages.success(request, _("Your comment has been posted."))
                return redirect('project_detail', slug=project.slug)

        # 4. Report Action
        elif action == 'report':
            report_form = ReportForm(request.POST)
            if report_form.is_valid():
                report = report_form.save(commit=False)
                report.reporter = request.user
                report.project = project
                comment_id = request.POST.get('reported_comment_id')
                if comment_id and comment_id.isdigit():
                    target_comment = Comment.objects.filter(id=int(comment_id)).first()
                    if target_comment:
                        report.comment = target_comment
                        report.project = None
                report.save()
                messages.info(request, _("Thank you for reporting. Our moderation team will review this report."))
                return redirect('project_detail', slug=project.slug)

    # 4 Similar Projects based on matching tags
    project_tags = project.tags.all()
    if project_tags.exists():
        similar_projects = Project.objects.filter(
            tags__in=project_tags,
            is_cancelled=False
        ).exclude(id=project.id).distinct().select_related('category', 'creator')[:4]
    else:
        similar_projects = Project.objects.filter(
            category=project.category,
            is_cancelled=False
        ).exclude(id=project.id).select_related('category', 'creator')[:4]

    # Top-level comments only
    top_comments = project.comments.filter(parent__isnull=True).order_by('-created_at')

    context = {
        'project': project,
        'donation_form': donation_form,
        'comment_form': comment_form,
        'report_form': report_form,
        'similar_projects': similar_projects,
        'top_comments': top_comments,
        'user_rating': user_rating,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_create_view(request):
    if request.method == 'POST':
        project_form = ProjectForm(request.POST, request.FILES)
        gallery_form = ProjectGalleryImagesForm(request.POST, request.FILES)

        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.creator = request.user
            project.save()

            # Process Tags
            tag_names_raw = project_form.cleaned_data.get('tag_names', '')
            if tag_names_raw:
                raw_tags = [t.strip().lstrip('#') for t in tag_names_raw.split(',') if t.strip()]
                for name in raw_tags:
                    tag_obj, _created = Tag.objects.get_or_create(name__iexact=name, defaults={'name': name})
                    project.tags.add(tag_obj)

            # Process Gallery Images
            uploaded_images = request.FILES.getlist('images')
            for img in uploaded_images:
                ProjectImage.objects.create(project=project, image=img)

            messages.success(request, _("Congratulations! Your crowd-funding campaign has been launched successfully."))
            return redirect('project_detail', slug=project.slug)
        else:
            messages.error(request, _("Please fix the errors in the project form below."))
    else:
        project_form = ProjectForm()
        gallery_form = ProjectGalleryImagesForm()

    return render(request, 'projects/project_create.html', {
        'project_form': project_form,
        'gallery_form': gallery_form,
    })


@login_required
def project_cancel_view(request, slug):
    project = get_object_or_404(Project, slug=slug, creator=request.user)

    if project.is_cancelled:
        messages.info(request, _("This campaign has already been cancelled."))
        return redirect('project_detail', slug=project.slug)

    if project.can_be_cancelled:
        project.is_cancelled = True
        project.save(update_fields=['is_cancelled'])
        messages.success(request, _("Your campaign has been cancelled successfully as donations were under 25% of the target."))
    else:
        messages.error(request, _("Campaign cannot be cancelled because donations have reached or exceeded 25% of the target amount."))

    return redirect('project_detail', slug=project.slug)
