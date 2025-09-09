from django.urls import path, include
from rest_framework.routers import DefaultRouter
from seeker import views

router = DefaultRouter()
router.register(r'profile', views.SeekerProfileViewSet)
router.register(r'resume', views.ResumeViewSet)
router.register(r'experience', views.ExperienceViewSet)

urlpatterns = [
    path('', include(router.urls)),  # <-- Make sure this is used
]
