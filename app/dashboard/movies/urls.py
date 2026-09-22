from django.urls import path

from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/<int:movie_id>/', views.movie_api, name='movie_api'),
    path('events/', views.movie_events, name='movie_events'),
]
