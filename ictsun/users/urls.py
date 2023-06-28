from django.contrib.auth import views as django_views
from django.urls import path, include

from . import views


urlpatterns = [
    path('login/', views.LogIn.as_view(), name='loginview'),
    path('logout/', django_views.LogoutView.as_view(), name='logout'),       #this is exatly like rest_framework/urls
    path('signup/', views.SignUp.as_view(), name='signupview'),
    path('userchange/', views.UserChange.as_view(), name='user-change'),
    path('profile/<user_id>/',  views.UserProfile.as_view(), name='user-profile'),
    path('profile/admin/<id>/',  views.AdminProfile.as_view(), name='admin-profile'),     #we used this url for main/my_serializers/PostListSerializer/get_author()
]

