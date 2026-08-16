from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/chat/', views.chat_api_view, name='chat_api'),
]
