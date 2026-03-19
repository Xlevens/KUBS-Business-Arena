from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'rounds', views.RoundViewSet, basename='round')
router.register(r'contestants', views.ContestantViewSet, basename='contestant')
router.register(r'register', views.RegistrationViewSet, basename='registration')
router.register(r'points', views.PointTransactionViewSet, basename='points')
router.register(r'leaderboard', views.LeaderboardViewSet, basename='leaderboard')

urlpatterns = [
    # Frontend pages
    path('', views.introduction, name='introduction'),
    path('register/', views.register, name='register'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('dashboard/', views.round_head_dashboard, name='dashboard'),

    # REST API
    path('api/', include(router.urls)),
]
