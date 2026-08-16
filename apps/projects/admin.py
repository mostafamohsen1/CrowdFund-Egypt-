from django.contrib import admin
from .models import Category, Tag, Project, ProjectImage, Donation, Comment, Rating, Report


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'creator', 'total_target', 'current_donations', 'percentage_raised', 'is_featured', 'is_cancelled', 'created_at']
    list_filter = ['is_featured', 'is_cancelled', 'category', 'created_at']
    search_fields = ['title', 'details', 'creator__email', 'creator__first_name']
    list_editable = ['is_featured', 'is_cancelled']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    filter_horizontal = ['tags']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'amount', 'donated_at']
    list_filter = ['donated_at']
    search_fields = ['project__title', 'user__email']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user__email', 'project__title']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'project', 'comment', 'reason', 'created_at']
    list_filter = ['created_at']
    search_fields = ['reason', 'reporter__email']
