from django.db import models
from django.contrib.auth.models import User
import uuid
import pandas as pd
import os
from django.utils.translation import gettext as _
# Create your models here.

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=500, blank=True, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    short_intro = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(
        null=True, blank=True, upload_to='profiles/', default="profiles/user-default.png")
    social_github = models.CharField(max_length=200, blank=True, null=True)
    social_twitter = models.CharField(max_length=200, blank=True, null=True)
    social_linkedin = models.CharField(max_length=200, blank=True, null=True)
    social_youtube = models.CharField(max_length=200, blank=True, null=True)
    social_website = models.CharField(max_length=200, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)

    def __str__(self):
        return str(self.username)

    class Meta:
        ordering = ['created']

    @property
    def imageURL(self):
        try:
            url = self.profile_image.url
        except:
            url = ''
        return url









class Skill(models.Model):
    owner = models.ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)

    def __str__(self):
        return str(self.name)


class Message(models.Model):
    sender = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True)
    recipient = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False, null=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ['is_read', '-created']




class Formation(models.Model):

    # Définition des champs du modèle
    name = models.CharField(_("Name"), max_length=100)
    school = models.CharField(_("School"), max_length=100)
    difficulty_level = models.CharField(_("Difficulty Level"), max_length=100)
    rating = models.CharField(_("Rating"), max_length=100)
    link = models.CharField(_("Link"), max_length=100)
    about = models.TextField(_("About"))

def __str__(self):
        return self.name
    
    
class fraudTrain(models.Model):
    trans_date_trans_time = models.DateTimeField()
    cc_num = models.CharField( max_length=20)
    merchant = models.CharField( max_length=100)
    category = models.CharField(max_length=100)
    amt = models.DecimalField(max_digits=10, decimal_places=2)
    first = models.CharField(max_length=50)
    last = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    street = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip = models.CharField(max_length=20)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    long = models.DecimalField(max_digits=9, decimal_places=6)
    city_pop = models.IntegerField()
    job = models.CharField( max_length=100)
    dob = models.DateField()
    trans_num = models.CharField( max_length=100)
    unix_time = models.BigIntegerField()
    merch_lat = models.DecimalField(max_digits=9, decimal_places=6)
    merch_long = models.DecimalField(max_digits=9, decimal_places=6)
    is_fraud = models.BooleanField()

    def __str__(self):
        return self.id