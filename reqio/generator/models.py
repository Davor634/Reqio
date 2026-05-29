from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)

class SRSDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thread_id = models.CharField(max_length = 150)
    name = models.CharField(max_length=255)
    prompt = models.CharField(max_length=1023)
    document = models.JSONField(null=True)
    changed_document = models.JSONField(null=True)
    questions = models.JSONField()