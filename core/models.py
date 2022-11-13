from django.db import models
# from django.contrib.auth.models import (
#     BaseUserManager, AbstractBaseUser
# )
# import six
from mptt.models import MPTTModel, TreeForeignKey
from django.dispatch import receiver
from PIL import Image as Img
from PIL import ExifTags
from io import BytesIO
import os, shutil
from django.core.files import File
from django.db.models.signals import post_save
from django.conf import settings
# from django.utils import timezone

from utils.utils import rotate_image
from accounts.models import User, Photographer
from mptt.models import MPTTModel, TreeForeignKey
import re
import math

STATUS_CHOICES = [('accepted', 'accepted'), ('registered', 'registered'), ('nonregistered', 'nonregistered'),
                  ('unplaced', 'unplaced'), ('published', 'published'), ('trade', 'trade')]

class Taxonomy(models.Model):
    class Meta:
        unique_together = (("taxon", "parent_name"),)
        ordering = ['taxon','parent_name']
    taxon = models.CharField(db_column='taxon', max_length=50, default='',null=False, blank=False)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    parent_name = models.CharField(max_length=50, null=True)
    rank = models.CharField(max_length=20, null=True, blank=True)
    level = models.IntegerField(null=True)
    def __str__(self):
        return self.taxon


class Taxonomy1(models.Model):
    class Meta:
        unique_together = (("taxon", "parent_name"),)
        ordering = ['taxon','parent_name']
    taxon = models.CharField(db_column='taxon', max_length=50, default='',null=False, blank=False)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    parent_name = models.CharField(max_length=50, null=True)
    rank = models.CharField(max_length=20, null=True, blank=True)
    level = models.IntegerField(null=True)
    def __str__(self):
        return self.taxon


class Family(models.Model):
    family = models.CharField(primary_key=True, default='', db_column='family', max_length=50)
    orig_pid = models.CharField(max_length=20, null=True, blank=True)
    author = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    application = models.CharField(max_length=50, default='', null=True, blank=True)
    common_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    order = models.CharField(max_length=20, null=True)
    kingdom = models.CharField(max_length=20, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='')
    source = models.CharField(max_length=20, null=True)
    active = models.BooleanField(null=True, default=False)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.family

    class Meta:
        ordering = ['family']


class Subfamily(models.Model):
    family = models.ForeignKey(Family, null=True, blank=True, db_column='family', on_delete=models.DO_NOTHING)
    subfamily = models.CharField(primary_key=True, max_length=50, default='', db_column='subfamily')
    author = models.CharField(max_length=200, blank=True, default='')
    year = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    num_genus   = models.IntegerField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.subfamily

    class Meta:
        ordering = ['subfamily']


class Tribe(models.Model):
    family = models.ForeignKey(Family, default='', db_column='family', on_delete=models.DO_NOTHING)
    tribe = models.CharField(primary_key=True, default='', db_column='tribe', max_length=50)
    author = models.CharField(max_length=200, blank=True)
    year = models.IntegerField(null=True, blank=True)
    subfamily = models.ForeignKey(Subfamily, null=True, default='', db_column='subfamily', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    num_genus   = models.IntegerField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.tribe

    class Meta:
        ordering = ['tribe']


class Subtribe(models.Model):
    family = models.ForeignKey(Family, default='', db_column='family', on_delete=models.DO_NOTHING)
    subtribe = models.CharField(max_length=50, primary_key=True, default='', db_column='subtribe')
    author = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    subfamily = models.ForeignKey(Subfamily, null=True, default='', db_column='subfamily', on_delete=models.DO_NOTHING)
    tribe = models.ForeignKey(Tribe, null=True, default='', db_column='tribe', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True, blank=True)
    num_genus   = models.IntegerField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.subtribe

    class Meta:
        ordering = ['subtribe']


class Country(models.Model):
    # class Meta:
    #     unique_together = (("dist_code", "dist_num", "region"),)
    #     ordering = ['country','region']
    dist_code = models.CharField(max_length=3, primary_key=True)
    dist_num = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    orig_code = models.CharField(max_length=100, null=True, blank=True)
    uncertainty = models.CharField(max_length=10, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)


class Continent(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    note = models.CharField(max_length=500, null=True, blank=True)
    source = models.CharField(max_length=10, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Region(models.Model):
    id = models.IntegerField(primary_key=True)
    continent = models.ForeignKey(Continent, db_column='continent', on_delete=models.DO_NOTHING, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    note = models.CharField(max_length=500, null=True, blank=True)
    source = models.CharField(max_length=10, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class SubRegion(models.Model):
    continent = models.ForeignKey(Continent, default=0, db_column='continent', on_delete=models.DO_NOTHING, null=True,
                                  blank=True)
    region = models.ForeignKey(Region, db_column='region', on_delete=models.DO_NOTHING, null=True, blank=True)
    code = models.CharField(primary_key=True, max_length=10, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    note = models.CharField(max_length=500, null=True, blank=True)
    source = models.CharField(max_length=10, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class LocalRegion(models.Model):
    id = models.IntegerField(primary_key=True)
    continent = models.ForeignKey(Continent, null=True, blank=True, db_column='continent', on_delete=models.DO_NOTHING)
    region = models.ForeignKey(Region, null=True, blank=True, db_column='region', on_delete=models.DO_NOTHING)
    subregion_code = models.ForeignKey(SubRegion, null=True, blank=True, db_column='subregion_code',
                                       on_delete=models.DO_NOTHING)
    continent_name = models.CharField(max_length=100, null=True)
    region_name = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=100, null=True, unique=True)
    code = models.CharField(max_length=100, null=True, blank=True)
    note = models.CharField(max_length=500, null=True, blank=True)
    source = models.CharField(max_length=10, null=True, blank=True)
    subregion = models.CharField(max_length=10, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class GeoLocation(MPTTModel):
    name = models.CharField(max_length=50, unique=True, null=True, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Donation(models.Model):
    class Sources:
        STRIPE = 'Stripe'
        PAYPAL = 'Paypal'
        CHOICES = (
            (STRIPE, 'Stripe'),
            (PAYPAL, 'Paypal')
        )

    class Statuses:
        ACCEPTED = "Accepted"
        REJECTED = "Rejected"
        CANCELLED = "Cancelled"
        REFUNDED = "Refunded"
        PENDING = "Pending"
        UNVERIFIED = "Unverified"
        CHOICES = [
            (ACCEPTED, "Accepted"),
            (REJECTED, "Rejected"),
            (CANCELLED, "Cancelled"),
            (REFUNDED, "Refunded"),
            (PENDING, "Pending"),
            (UNVERIFIED, "Unverified"),
        ]

    source = models.CharField(max_length=10, choices=Sources.CHOICES, default=Sources.STRIPE)
    source_id = models.CharField(max_length=255, blank=True, null=True)
    donor_name = models.CharField(max_length=255, blank=True, null=True)
    donor_display_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, choices=Statuses.CHOICES, default=Statuses.UNVERIFIED)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    country_code = models.CharField(max_length=2, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"Donation made by {self.donor_display_name} - ${self.amount}"
