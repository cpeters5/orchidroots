# Create your models here.
from django.db import models
from django.conf import settings
from accounts.models import User, Profile

# import uuid
RANK_CHOICES = [(i, str(i)) for i in range(0, 10)]
QUALITY_CHOICES = ((1, 'Top'), (2, 'High'), (3, 'Average'), (4, 'Low'),)  # (5, 'Challenged'),)
STATUS_CHOICES = (('NFS','not for sale'),('AV','available'),('PUR','price upon request'))

class City(models.Model):
    city = models.CharField(primary_key=True, db_column='city', max_length=200)
    description = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.city


class Gallery(models.Model):
    gallery_name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.ForeignKey(City, db_column='city', related_name='galcity', default='', on_delete=models.DO_NOTHING)
    url = models.URLField(max_length=200, null=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.gallery_name



class Artist(models.Model):
    artist = models.CharField(primary_key=True, default='', db_column='artist', max_length=50)
    user_id = models.OneToOneField(User, db_column='user_id', null = True,on_delete=models.SET_NULL)
    statement = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=200)
    city = models.ForeignKey(City, db_column='city', related_name='artcity', default='', on_delete=models.DO_NOTHING)
    url = models.URLField(max_length=200, null=True)
    profile_pic_path = models.ImageField(upload_to="images/user_profile/", null=True, blank=True)
    media = models.CharField(max_length=200, null=True, blank=True)
    genre = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.artist

    def image_dir(self):
        return "/media/"

    def get_best_image(self):
        img = Artwork.objects.filter(artist=self.artist).order_by('-rank', '?')
        if img.count() > 0:
            img = img[0:1][0]
            return img
        return None

    def image_dir(self):
        return "/media/"


    def get_profile_pic(self):
        profile_pic_path = Profile.objects.get(user_id=self.user_id).profile_pic_path
        return profile_pic_path

class Medium(models.Model):
    medium = models.CharField(primary_key=True, default='', db_column='medium', max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.medium


class Genre(models.Model):
    genre = models.CharField(primary_key=True, default='', db_column='genre', max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.genre

# detail
class Artwork(models.Model):
    artist = models.ForeignKey(Artist, db_column='artist', related_name='artistwork', default='', on_delete=models.DO_NOTHING)
    medium = models.ForeignKey(Medium, db_column='medium', related_name='artistmedium', default='', on_delete=models.DO_NOTHING)
    genre = models.ForeignKey(Genre, db_column='genre', related_name='artistgenre', default='', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=200, blank=True)
    support = models.CharField(max_length=200, blank=True)
    hashtag = models.CharField(max_length=200, blank=True)
    style = models.CharField(max_length=200, blank=True)
    price = models.IntegerField(blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='')
    source_url = models.CharField(max_length=200, null=True, blank=True)
    rank = models.IntegerField(choices=RANK_CHOICES,default=5)
    date = models.DateField(null=True)
    description = models.TextField(null=True, blank=True)
    image_file = models.ImageField(upload_to="gallery/artworks/")
    # image_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    def image_dir(self):
        return "/media/"



# old
