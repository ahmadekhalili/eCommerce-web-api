from django.contrib.auth import views as django_views
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.LogIn.as_view(), name='loginview'),
    path('logout/', django_views.LogoutView.as_view(), name='logout'),       #this is exatly like rest_framework/urls
    path('sendsms/', views.SendSMS.as_view(), name='sendsms'),
    path('signup/', views.SignUp.as_view(), name='signupview'),
    path('signup/<int:pk>/', views.SignUp.as_view(), name='signup-update'),
    path('update/', views.UserUpdate.as_view(), name='user-change'),
    path('profile/<user_id>/',  views.UserProfile.as_view(), name='user-profile'),
    path('profile/admin/<int:pk>/',  views.AdminProfile.as_view(), name='admin-profile'),     #we used this url for main/my_serializers/PostMongoSerializer.author
]

