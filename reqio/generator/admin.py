from django.contrib import admin
from .models import Profile, SRSDocument
from django.contrib.auth.models import User

# Register your models here.

admin.site.register(SRSDocument)
admin.site.register(Profile)