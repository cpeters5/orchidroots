from django.db import models
from django.apps import apps
from accounts.models import User, Photographer
from mptt.models import MPTTModel, TreeForeignKey

RANK_CHOICES = [(i, str(i)) for i in range(0, 10)]

STATUS_CHOICES = [('accepted', 'accepted'), ('registered', 'registered'), ('nonregistered', 'nonregistered'),
                  ('unplaced', 'unplaced'), ('published', 'published'), ('trade', 'trade')]


class Family(models.Model):
    family = models.CharField(primary_key=True, default='', db_column='family', max_length=50)
    orig_pid = models.CharField(max_length=20, null=True, blank=True)
    author = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    application = models.CharField(max_length=50, default='', null=True, blank=True)
    common_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    order = models.CharField(max_length=20, null=True)
    clss = models.CharField(max_length=20, null=True)
    kingdom = models.CharField(max_length=20, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='')
    source = models.CharField(max_length=20, null=True)
    active = models.BooleanField(null=True, default=False)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.family

    def get_best_img(self):
        Genus = apps.get_model(self.application, 'Genus')
        genus_list = Genus.objects.filter(family=self.family).filter(num_spcimage__gt=0).order_by('?')
        for img in genus_list:
            if img.get_best_img():
                return img.get_best_img()
        return None

    class Meta:
        ordering = ['family']


class Subfamily(models.Model):
    family = models.ForeignKey(Family, null=True, blank=True, db_column='family', on_delete=models.DO_NOTHING)
    subfamily = models.CharField(primary_key=True, max_length=50, default='', db_column='subfamily')
    author = models.CharField(max_length=200, blank=True, default='')
    year = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='')
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


class UploadFile(models.Model):
    pid        = models.BigIntegerField(db_column='pid')
    family = models.ForeignKey(Family, null=True, db_column='family', related_name='spcomfamily', on_delete=models.DO_NOTHING)
    author     = models.ForeignKey(Photographer, db_column='author', related_name='cocauthor', null=True, blank=True,on_delete=models.DO_NOTHING)
    user_id    = models.ForeignKey(User, db_column='user_id', related_name='cocuser_id1', null=True, blank=True,on_delete=models.DO_NOTHING)
    credit_to  = models.CharField(max_length=100, null=True, blank=True)    #should match author_id inPhotography
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    source_file_name = models.CharField(max_length=100, null=True, blank=True)
    name        = models.CharField(max_length=100, null=True, blank=True)
    awards      = models.CharField(max_length=200, null=True, blank=True)
    variation   = models.CharField(max_length=50, null=True, blank=True)
    forma       = models.CharField(max_length=50, null=True, blank=True)
    originator  = models.CharField(max_length=50, null=True, blank=True)
    text_data   = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    certainty   = models.CharField(max_length=20, null=True, blank=True)
    type        = models.CharField(max_length=20, null=True, blank=True)
    location    = models.CharField(max_length=100, null=True, blank=True)
    rank        = models.IntegerField(choices=RANK_CHOICES,default=0)
    image_file_path = models.ImageField(upload_to='images/', null=True, blank=True)
    image_file  = models.CharField(max_length=100, null=True, blank=True)
    is_private  = models.BooleanField(null=True, default=False)
    approved    = models.BooleanField(null=True, default=False)
    compressed  = models.BooleanField(null=True, default=False)
    block_id    = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.name()


class DataSource(models.Model):
    source = models.CharField(max_length=20, primary_key=True)
    organization = models.CharField(max_length=1000, null=True, blank=True)
    source_home = models.CharField(max_length=1000, null=True, blank=True)
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    source_name = models.CharField(max_length=100, null=True, blank=True)
    short_description = models.CharField(max_length=100, null=True, blank=True)
    citing = models.TextField(null=True)
    description = models.TextField(null=True)
    collaboration = models.TextField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.source


LEVEL_CHOICES = [('Family', 'Family'), ('Genus', 'Genus'), ('Accepted', 'Accepted')]
APPLICATION_CHOICES = [('animalia', 'animalia'), ('aves', 'aves'), ('fungi', 'fungi'), ('other', 'other'), ('orchidaceae', 'orchidaceae')]

class CommonName(models.Model):
    common_name = models.CharField(max_length=500, null=True, blank=True)
    common_name_search = models.CharField(max_length=500, null=True, blank=True)
    application = models.CharField(max_length=20, choices=APPLICATION_CHOICES, default='')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='')
    taxon_id = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.common_name

    def get_best_img(self):
        if self.level == 'Accepted':
            app = self.application
            Species = apps.get_model(app, 'Species')
            try:
                species = Species.objects.get(pk=self.taxon_id)
                return species.get_best_img()
            except Species.DoesNotExist:
                return None
        return None


class Binomial(models.Model):
    genus = models.CharField(max_length=200, null=True, blank=True)
    binomial = models.CharField(max_length=200, null=True, blank=True)
    binomial_search = models.CharField(max_length=200, null=True, blank=True)
    species = models.CharField(max_length=200, null=True, blank=True)
    species_search = models.CharField(max_length=200, null=True, blank=True)
    application = models.CharField(max_length=20, choices=APPLICATION_CHOICES, default='')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='')
    taxon_id = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self):
        return self.binomial

    def get_best_img(self):
        if self.level == 'Accepted':
            app = self.application
            Species = apps.get_model(app, 'Species')
            try:
                species = Species.objects.get(pk=self.taxon_id)
                return species.get_best_img()
            except Species.DoesNotExist:
                return None
        return None
