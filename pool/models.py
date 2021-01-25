from django.db import models
# from django.contrib.auth.models import (
#     BaseUserManager, AbstractBaseUser
# )
# import six
# from mptt.models import MPTTModel, TreeForeignKey
from django.dispatch import receiver
from PIL import Image as Img
from PIL import ExifTags
# from io import BytesIO
# import os, shutil
# from django.core.files import File
# from django.db.models.signals import post_save
from django.conf import settings
# from django.utils import timezone

from accounts.models import User, Photographer
from core.models import Family, Subfamily, Tribe, Subtribe, Country, Region, Continent, SubRegion, LocalRegion
# from orchiddb.models import Family, Subfamily, Tribe, Subtribe, Subgenus, Section, Subsection, Series, Country, Region, Continent, SubRegion, LocalRegion
import re
import math

RANK_CHOICES = [(i, str(i)) for i in range(0, 10)]
QUALITY = (
    (1, 'Top'),
    (2, 'High'),
    (3, 'Average'),
    (4, 'Low'),
    # (5, 'Challenged'),
)

STATUS_CHOICES = [('accepted', 'accepted'), ('registered', 'registered'), ('nonregistered', 'nonregistered'),
                  ('unplaced', 'unplaced'), ('published', 'published'), ('trade', 'trade')]
TYPE_CHOICES = [('species', 'species'), ('hybrid', 'hybrid')]


class Genus(models.Model):
    pid = models.BigIntegerField(primary_key=True)
    is_hybrid = models.CharField(max_length=1, null=True)
    genus = models.CharField(max_length=50, default='', unique=True)
    author = models.CharField(max_length=200, default='')
    citation = models.CharField(max_length=200, default='')
    cit_status = models.CharField(max_length=20, null=True)
    alliance = models.CharField(max_length=50, default='')
    family = models.ForeignKey(Family, null=True, db_column='family', related_name='othfamily', on_delete=models.DO_NOTHING)
    subfamily = models.ForeignKey(Subfamily, null=True, default='', db_column='subfamily', related_name='othsubfamily', on_delete=models.DO_NOTHING)
    tribe = models.ForeignKey(Tribe, null=True, default='', db_column='tribe', related_name='othtribe', on_delete=models.DO_NOTHING)
    subtribe = models.ForeignKey(Subtribe, null=True, default='', db_column='subtribe', related_name='othsubtribe', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=20, default='')
    type = models.CharField(max_length=20, default='')
    description = models.TextField(null=True)
    distribution = models.TextField(null=True)
    text_data = models.TextField(null=True)
    source = models.CharField(max_length=50, default='')
    abrev = models.CharField(max_length=50, default='')
    year = models.IntegerField(null=True)
    num_species = models.IntegerField(null=True, default=0)
    num_species_synonym = models.IntegerField(null=True, default=0)
    num_species_total = models.IntegerField(null=True, default=0)
    num_hybrid = models.IntegerField(null=True, default=0)
    num_hybrid_synonym = models.IntegerField(null=True, default=0)
    num_hybrid_total = models.IntegerField(null=True, default=0)
    num_synonym = models.IntegerField(null=True, default=0)
    num_spcimage = models.IntegerField(null=True, default=0)
    num_spc_with_image = models.IntegerField(null=True, default=0)
    pct_spc_with_image = models.DecimalField(decimal_places=2, max_digits=7, null=True, default=0)
    num_hybimage = models.IntegerField(null=True, default=0)
    num_hyb_with_image = models.IntegerField(null=True, default=0)
    pct_hyb_with_image = models.DecimalField(decimal_places=2, max_digits=7, null=True, default=0)
    notepad = models.CharField(max_length=500, default='')
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.genus

    def fullname(self):
        fname = self.genus
        if self.author:
            fname = fname + self.author
        if self.year:
            fname = fname + ' ' + self.year
        return fname

    def get_status(self):
        return self.status

    def get_description(self):
        return self.description

    def getAccepted(self):
        if 'synonym' in self.status:
            acc_id = Gensyn.objects.get(pid=self.pid).acc_id
            gen = Genus.objects.get(pid=acc_id)
            return "<i>%s</i> %s" % (gen.genus, gen.author)

    def getAcc(self):
        if 'synonym' in self.status:
            acc_id = Gensyn.objects.get(pid=self.pid).acc_id
            if acc_id:
                gen = Genus.objects.get(pid=acc_id)
                return gen.genus
            else:
                return "No accepted name found for this synonym."

    def getGenid(self):
        if 'synonym' in self.status:
            syn = Gensyn.objects.get(pid=self.pid).acc_id
            return "%s" % syn

    def getSynAuth(self):
        if 'synonym' in self.status:
            syn = Gensyn.objects.get(pid=self.pid).acc_author
            return "%s" % syn

    def get_roundspcpct(self):
        if self.pct_spc_with_image > 0:
            return round(self.pct_spc_with_image)
        else:
            return None

    def get_roundhybpct(self):
        if self.pct_hyb_with_image > 0:
            return round(self.pct_hyb_with_image)
        else:
            return None

    class Meta:
        # verbose_name_plural = "Anni"
        ordering = ('genus',)


class Species(models.Model):
    pid = models.BigIntegerField(primary_key=True)
    source = models.CharField(max_length=10)
    genus = models.CharField(max_length=50)
    is_hybrid = models.CharField(max_length=1, null=True)
    species = models.CharField(max_length=50)
    infraspr = models.CharField(max_length=20, null=True)
    infraspe = models.CharField(max_length=50, null=True)
    author = models.CharField(max_length=200)
    originator = models.CharField(max_length=100, blank=True)
    scientific_name = models.CharField(max_length=500, blank=True)
    citation = models.CharField(max_length=200)
    cit_status = models.CharField(max_length=20, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='')
    year = models.IntegerField(null=True)
    date = models.DateField(null=True)
    distribution = models.TextField(blank=True)
    physiology = models.CharField(max_length=200, blank=True)
    url = models.CharField(max_length=200, blank=True)
    url_name = models.CharField(max_length=100, blank=True)
    num_image = models.IntegerField(blank=True)
    num_ancestor = models.IntegerField(null=True, blank=True)
    num_species_ancestor = models.IntegerField(null=True, blank=True)
    num_descendant = models.IntegerField(null=True, blank=True)
    num_dir_descendant = models.IntegerField(null=True, blank=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='othgen', default=0, on_delete=models.DO_NOTHING)
    notepad = models.CharField(max_length=500, default='')
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)
    description = models.TextField(null=True, blank=True)

    # TODO: add reference column
    def __str__(self):
        name = self.species
        if self.infraspr:
            name = '%s %s %s' % (name, self.infraspr, self.infraspe)
        return name

    def speciesname(self):
        if self.type == 'species' or self.is_hybrid:
            spc = '<i>%s</i>' % self.species
            if self.is_hybrid:
                spc = '%s %s' % (self.is_hybrid, spc)
        elif self.type == 'hybrid':
            spc = re.sub('Memoria', 'Mem.', self.species.rstrip())
        else:
            spc = '<i>%s</i>' % self.species

        if self.infraspr:
            spc = '%s %s <i>%s</i>' % (spc, self.infraspr, self.infraspe)
        return spc

    def fullspeciesname(self):
        if self.type == 'species' or self.is_hybrid:
            spc = '<i>%s</i>' % self.species
            if self.is_hybrid:
                spc = '%s %s' % (self.is_hybrid, spc)
        else:
            spc = '<i>%s</i>' % self.species

        if self.infraspr:
            spc = '%s %s <i>%s</i>' % (spc, self.infraspr, self.infraspe)

        return spc

    def textspeciesname(self):
        spc = re.sub('Memoria', 'Mem.', self.species.rstrip())
        if self.infraspr:
            spc = '%s %s %s' % (self.species, self.infraspr, self.infraspe)
        if self.is_hybrid:
            spc = '%s %s' % (self.is_hybrid, spc)
        return spc

    def textspeciesnamefull(self):
        spc = self.species.rstrip()
        if self.infraspr:
            spc = '%s %s %s' % (self.species, self.infraspr, self.infraspe)
        if self.is_hybrid:
            spc = '%s %s' % (self.is_hybrid, spc)
        return spc

    def shortspeciesname(self):
        return '%s %s' % (self.genus, self.species)

    def textname(self):
        return '%s %s' % (self.genus, self.textspeciesname())

    def name(self):
        return '<i>%s</i> %s' % (self.genus, self.speciesname())

    def abrevname(self):
        return '<i>%s</i> %s' % (self.gen.abrev, self.speciesname())

    def namecasual(self):
        namecasual = self.abrevname()
        namecasual = re.sub('Memoria', 'Mem.', namecasual.rstrip())
        return namecasual

    def get_species(self):
        name = '%s' % (self.species)
        if self.is_hybrid:
            name = '%s %s' % (self.is_hybrid, name)
        if self.infraspr:
            name = '%s %s %s' % (name, self.infraspr, self.infraspe)
        return name

    def getAccepted(self):
        if 'synonym' in self.status:
            return Synonym.objects.get(pk=self.pid).acc
        return None

    def getAcc(self):
        if self.status == 'synonym':
            spid = Synonym.objects.get(spid=self.pid)
            return spid.acc_id
        return "Not a synonym."

    def getAbrevName(self):
        name = self.species
        name = re.sub('Memoria', 'Mem.', name.rstrip())
        if self.gen.abrev:
            if self.infraspe:
                name = self.gen.abrev + ' ' + name + ' ' + self.infraspr + ' ' + self.infraspe
            else:
                name = self.gen.abrev + ' ' + name
        else:
            name = self.name()
        return name

    def grex(self):
        if self.infraspe:
            return str(self.genus) + ' ' + str(self.species) + ' ' + str(self.infraspr) + ' ' + str(self.infraspe)
        else:
            return str(self.genus) + ' ' + str(self.species)

    def short_grex(self):
        if self.infraspe:
            return str(self.species) + ' ' + str(self.infraspr) + ' ' + str(self.infraspe)
        else:
            return str(self.species)

    def sourceurl(self):
        if self.source == 'Kew':
            return "https://wcsp.science.kew.org/namedetail.do?name_id=" + str(self.pid)
        elif self.source == 'RHS':
            return "http://apps.rhs.org.uk/horticulturaldatabase/orchidregister/orchiddetails.asp?ID=" + str(
                self.pid - 100000000)
        else:
            return "#"

    def get_best_img(self):
        if self.type == 'species':
            img = SpcImages.objects.filter(pid=self.pid).filter(image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')
        else:
            img = HybImages.objects.filter(pid=self.pid).filter(image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')

        if img.count() > 0:
            img = img[0:1][0]
            return img
        return None

    def get_best_img_by_author(self, author):
        if self.type == 'species':
            img = SpcImages.objects.filter(pid=self.pid).filter(author_id=author).filter(
                image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')
        else:
            img = HybImages.objects.filter(pid=self.pid).filter(author_id=author).filter(
                image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')

        if img.count() > 0:
            img = img[0:1][0]
            return img
        return None


class SpcImages(models.Model):
    pid = models.ForeignKey(Species, null=False, db_column='pid', related_name='othpid',on_delete=models.DO_NOTHING)
    # pid = models.BigIntegerField(null=True, blank=True)
    author = models.ForeignKey(Photographer, db_column='author', related_name='othspcauthor', on_delete=models.DO_NOTHING)
    credit_to = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    quality = models.IntegerField(choices=QUALITY, default=3,)
    name = models.CharField(max_length=100, null=True, blank=True)
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    image_url = models.CharField(max_length=500, null=True, blank=True)
    text_data = models.TextField(null=True, blank=True)
    certainty = models.CharField(max_length=20, null=True, blank=True)
    rank = models.IntegerField(choices=RANK_CHOICES,default=5)
    zoom = models.IntegerField(default=0)
    form = models.CharField(max_length=50, null=True, blank=True)
    source_file_name = models.CharField(max_length=100, null=True, blank=True)
    spid = models.IntegerField(null=True, blank=True)
    awards = models.CharField(max_length=200, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    variation = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=20, null=True, blank=True)
    # width = models.FloatField(default=1)
    # height = models.FloatField(default=1)
    image_file = models.CharField(max_length=100, null=True, blank=True)
    image_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
    family = models.ForeignKey(Family, db_column='family', related_name='othspcfamily', on_delete=models.DO_NOTHING)
    download_date = models.DateField(null=True, blank=True)
    genus = models.CharField(max_length=50)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='othspcgen', null=True, blank=True,on_delete=models.DO_NOTHING)
    is_private = models.BooleanField(null=True, default=False)
    block_id = models.IntegerField(null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id',related_name='othspcuser_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    approved_by = models.ForeignKey(User, db_column='approved_by', related_name='othspc_approved_by', null=True, blank=True,on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.pid.textname()

    def imgname(self):
        if self.source_file_name:
            myname = '<i>%s</i>' % (self.source_file_name)
        else:
            myname = self.pid.pid.abrevname()
        if self.variation:
            myname = '%s %s ' % (myname, self.variation)
        if self.form:
            myname = '%s %s form ' % (myname, self.form)
        if self.certainty:
            myname = '%s %s ' % (myname, self.certainty)
        if self.name:
            myname = "%s '%s' " % (myname, self.name)
        if self.awards:
            myname = '%s %s' % (myname, self.awards)
        return myname

    def imginfo(self):
        myname = ''
        if self.variation:
            myname = '%s %s ' % (myname, self.variation)
        if self.form:
            myname = '%s %s form ' % (myname, self.form)
        if self.certainty:
            myname = '%s %s ' % (myname, self.certainty)
        if self.name:
            myname = "%s '%s' " % (myname, self.name)
        if self.awards:
            myname = '%s %s' % (myname, self.awards)
        return myname

    def fullimgname(self):
        if self.source_file_name:
            myname = self.source_file_name
        else:
            myname = self.pid.pid
        if self.variation:
            myname = '%s %s ' % (myname, self.variation)
        if self.form:
            myname = '%s %s form ' % (myname, self.form)
        if self.certainty:
            myname = '%s %s ' % (myname, self.certainty)
        if self.name:
            myname = "%s '%s' " % (myname, self.name)
        if self.awards:
            myname = '%s %s' % (myname, self.awards)
        return myname

    def abrev(self):
        return '%s' % Genus.objects.get(pk=self.gen_id).abrev

    def web(self):
        web = Photographer.objects.get(author_id=self.author)
        return web.web

    # TODO: add block_id
    def image_dir(self):
        return 'utils/images/species/'
        # return 'utils/images/hybrid/' + block_id + '/'

    def thumb_dir(self):
        return 'utils/images/species_thumb/'

    def get_displayname(self):
        if self.credit_to:
            return self.credit_to
        return self.author.displayname

    def get_userid(self):
        author = Photographer.objects.get(author=self.author_id)
        return author.user_id


