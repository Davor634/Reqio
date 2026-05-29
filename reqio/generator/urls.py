from django.contrib import admin
from django.urls import path, include
from .views import home, signup, profile, load_saved, app_detail, save, create, assistant_response, submit_questions,change,apply,delete


app_name="generator"
urlpatterns = [
    path('', home, name="home"),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup', signup, name="signup"),
    path('profile/', profile, name="profile"),
    path('saved/', load_saved, name="saved"),
    path('app_detail/<int:app_id>/', app_detail, name="app_detail"),
    path('app_detail/<int:app_id>/save', save, name="save"),
    path('create/', create, name="create"),
    path('ask/', assistant_response, name='assistant_response'),
    path('submit/', submit_questions, name="submit_questions"),
    path('app_detail/<int:app_id>/change', change, name="change"),
    path('app_detail/<int:app_id>/apply', apply, name="apply"),
    path('app_detail/<int:app_id>/delete', delete, name="delete"),
]