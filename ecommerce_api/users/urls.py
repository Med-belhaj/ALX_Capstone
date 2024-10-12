from django.urls import path, include
from .views import UserRegistrationView, UserViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('', include(router.urls)),
]





