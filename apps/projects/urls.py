from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list_view, name='project_list'),
    path('create/', views.project_create_view, name='project_create'),
    path('category/<slug:category_slug>/', views.category_projects_view, name='category_projects'),
    path('<slug:slug>/', views.project_detail_view, name='project_detail'),
    path('<slug:slug>/cancel/', views.project_cancel_view, name='project_cancel'),
]
