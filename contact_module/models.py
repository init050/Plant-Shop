from django.db import models

# Create your models here.

class ContactUs(models.Model):
    title = models.CharField(max_length=100, verbose_name='Title')
    email = models.EmailField(max_length=225, verbose_name='Email')