from django.db import models
from django.conf import settings
# Create your models here.


class City(models.Model):
    city = models.CharField(primary_key=True, db_column='city', max_length=200)
    description = models.CharField(max_length=200, null=True, blank=True)


class Gallery(models.Model):
    gallery_name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.ForeignKey(City, db_column='city', related_name='galcity', default='', on_delete=models.DO_NOTHING)
    url = models.URLField(max_length=200, null=True)
    description = models.CharField(max_length=200, null=True, blank=True)

