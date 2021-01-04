from django.db import models

# Create your models here.
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
from orchiddb.models import Family, Subfamily, Tribe, Subtribe, Subgenus, Section, Subsection, Series, Country, Region, Continent, SubRegion, LocalRegion
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
    pid = models.IntegerField(primary_key=True)
    is_hybrid = models.CharField(max_length=1, null=True)
    genus = models.CharField(max_length=50, default='', unique=True)
    author = models.CharField(max_length=200, default='')
    citation = models.CharField(max_length=200, default='')
    cit_status = models.CharField(max_length=20, null=True)
    alliance = models.CharField(max_length=50, default='')
    family = models.ForeignKey(Family, null=True, db_column='family', related_name='natfamily', on_delete=models.DO_NOTHING)
    subfamily = models.ForeignKey(Subfamily, null=True, default='', db_column='subfamily', related_name='natsubfamily', on_delete=models.DO_NOTHING)
    tribe = models.ForeignKey(Tribe, null=True, default='', db_column='tribe', related_name='nattribe', on_delete=models.DO_NOTHING)
    subtribe = models.ForeignKey(Subtribe, null=True, default='', db_column='subtribe', related_name='natsubtribe', on_delete=models.DO_NOTHING)
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


# class GenusRelation(models.Model):
#     gen = models.OneToOneField(Genus, db_column='gen', primary_key=True, on_delete=models.CASCADE)
#     genus = models.CharField(max_length=50, default='')
#     parentlist = models.CharField(max_length=500, null=True)
#     formula = models.CharField(max_length=500, null=True)
#
#     def get_parentlist(self):
#         x = self.parentlist.split('|')
#         return x


# class Gensyn(models.Model):
#     pid = models.OneToOneField(
#         Genus,
#         db_column='pid',
#         on_delete=models.CASCADE,
#         primary_key=True)
#     accepted = models.CharField(max_length=50, default='')
#     acc_author = models.CharField(max_length=50, default='')
#     acc_year = models.IntegerField(null=True)
#     status = models.CharField(max_length=20, default='')
#     type = models.CharField(max_length=20, default='')
#     description = models.CharField(max_length=255, default='')
#     source = models.CharField(max_length=50, default='')
#     abrev = models.CharField(max_length=50, default='')
#     acc = models.ForeignKey(Genus, verbose_name='genus', related_name='gen_id', null=True, on_delete=models.CASCADE)
#     created_date = models.DateTimeField(auto_now_add=True, null=True)
#     modified_date = models.DateTimeField(auto_now=True, null=True)
#
#     def __str__(self):
#         return self.pid
#
#         # def get_genid(self):
#         # return self.acc_id


class Species(models.Model):
    pid = models.IntegerField(primary_key=True)
    source = models.CharField(max_length=10)
    genus = models.CharField(max_length=50)
    is_hybrid = models.CharField(max_length=1, null=True)
    species = models.CharField(max_length=50)
    infraspr = models.CharField(max_length=20, null=True)
    infraspe = models.CharField(max_length=50, null=True)
    author = models.CharField(max_length=200)
    originator = models.CharField(max_length=100, blank=True)
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
    gen = models.ForeignKey(Genus, db_column='gen', default=0, on_delete=models.DO_NOTHING)
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

    def navbar_name(self):
        # name = self.speciesname()
        name = self.species
        if self.infraspr:
            name = name + ' ' + self.infraspr + ' ' + self.infraspe
        if self.is_hybrid:
            name = name + " (" + self.is_hybrid
            if self.year:
                name = name + " " + str(self.year)
            if self.num_image > 0:
                name = name + " #img " + str(self.num_image)
            return name + ")"
        elif self.year:
            name = name + " (" + str(self.year)
            if self.status == 'synonym':
                name = name + " syn"
            elif self.num_image and self.num_image > 0:
                name = name + " #img " + str(self.num_image)
            return name + ")"
        return name

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


class Accepted(models.Model):
    pid = models.OneToOneField(
        Species,
        db_column='pid',
        on_delete=models.CASCADE,
        primary_key=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='natgen_id', null=True, blank=True, on_delete=models.DO_NOTHING)
    genus = models.CharField(max_length=50)
    species = models.CharField(max_length=50)
    infraspr = models.CharField(max_length=20, null=True)
    infraspe = models.CharField(max_length=50, null=True)
    is_hybrid = models.CharField(max_length=1, null=True)
    distribution = models.TextField(blank=True)
    is_type = models.BooleanField(null=True, default=False)
    physiology = models.CharField(max_length=200, null=True, blank=True)
    url = models.CharField(max_length=200, null=True, blank=True)
    url_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    common_name = models.CharField(max_length=100, null=True, blank=True)
    local_name = models.CharField(max_length=100, null=True, blank=True)
    bloom_month = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    fragrance = models.CharField(max_length=50, null=True, blank=True)
    altitude = models.CharField(max_length=50, null=True, blank=True)

    history = models.TextField(null=True, blank=True)
    analysis = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    etymology = models.TextField(null=True, blank=True)
    culture = models.TextField(null=True, blank=True)

    subgenus = models.CharField(max_length=50, null=True, blank=True)
    section = models.CharField(max_length=50, null=True, blank=True)
    subsection = models.CharField(max_length=50, null=True, blank=True)
    series = models.CharField(max_length=50, null=True, blank=True)

    intrasource = models.CharField(max_length=10)

    num_image = models.IntegerField(null=True, blank=True)
    num_descendant = models.IntegerField(null=True, blank=True)
    num_dir_descendant = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)
    operator = models.ForeignKey(User, db_column='operator', related_name='natoperator', null=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.pid.name()


class Distribution(models.Model):
    id = models.AutoField(primary_key=True, default=10)
    pid = models.ForeignKey(Species, on_delete=models.CASCADE,db_column='pid',related_name='dist_pid')
    gen = models.ForeignKey(Genus, on_delete=models.DO_NOTHING,db_column='gen',related_name='dist_gen',null=True, blank=True)
    source = models.CharField(max_length=10, blank=True)
    continent_id = models.ForeignKey(Continent, db_column='continent_id', related_name='nat_continent_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    region_id = models.ForeignKey(Region, db_column='region_id',related_name='natregion_id',null=True, on_delete=models.DO_NOTHING)
    subregion_code = models.ForeignKey(SubRegion, db_column='subregion_code',related_name='natsubregion_id',null=True, on_delete=models.DO_NOTHING)
    dist_code = models.CharField(max_length=10, null=True)
    localregion_code = models.CharField(max_length=10, null=True)
    localregion_id = models.ForeignKey(LocalRegion, db_column='localregion_id',related_name='natlocalregion_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    orig_code = models.CharField(max_length=100,blank=True)
    dist_status = models.CharField(max_length=10,blank=True)
    confidence = models.CharField(max_length=10,blank=True)
    comment = models.CharField(max_length=500,blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = (("pid", "region_id","subregion_code","localregion_id"),)

    def name(self):
        name = ''
        if self.localregion_id and self.localregion_id.id > 0 and self.localregion_id.code != 'OO':
            name = name + self.localregion_id.name
            if self.subregion_code:
                name = name + ', ' + self.subregion_code.name + ', ' + self.continent_id.name
        elif self.subregion_code:
            name = name + self.subregion_code.name + ', ' + self.continent_id.name
        elif self.region_id:
            name = name + self.region_id.name
        elif self.continent_id:
            name = name + self.continent_id.name
        return name

    def __str__(self):
        return self.name()

    def subname(self):
        return self.subregion_code.name

    def regname(self):
        return self.region_id.name

    def locname(self):
        return self.localregion_id.name

    def conname(self):
        return self.continent_id.name


# Collection of intrageneric placements from diverse sources. May contain naturakl hybrid
class Synonym(models.Model):
    spid = models.OneToOneField(
        Species,
        related_name='spid',
        db_column='spid',
        on_delete=models.CASCADE,
        primary_key=True)
    acc = models.ForeignKey(Species, verbose_name='accepted genus', related_name='nataccid', on_delete=models.CASCADE)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='natgen', null=True, blank=True, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    genus = models.CharField(max_length=50, null=True, blank=True)
    is_hybrid = models.CharField(max_length=5, null=True, blank=True)
    species = models.CharField(max_length=50, null=True, blank=True)
    infraspr = models.CharField(max_length=20, null=True, blank=True)
    infraspe = models.CharField(max_length=50, null=True, blank=True)
    sgen = models.ForeignKey(Genus, db_column='sgen', related_name='natsgen', null=True, blank=True,
                             on_delete=models.DO_NOTHING)
    syear = models.IntegerField(null=True, blank=True)
    sgenus = models.CharField(max_length=50, null=True, blank=True)
    sis_hybrid = models.CharField(max_length=5, null=True, blank=True)
    sspecies = models.CharField(max_length=50, null=True, blank=True)
    sinfraspr = models.CharField(max_length=20, null=True, blank=True)
    sinfraspe = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.spid.name()

    def get_shortname(self):
        if self.sis_hybrid:
            if self.sinfraspe:
                return '%s %s %s %s %s' % (self.sgenus, self.sis_hybrid, self.sspecies,
                                           self.sinfraspr, self.sinfraspe)
            else:
                return '%s %s %s' % (self.sgenus, self.sis_hybrid, self.sspecies)
        else:
            if self.sinfraspe:
                return '%s %s %s %s' % (self.sgenus, self.sspecies,
                                        self.sinfraspr, self.sinfraspe)
            else:
                return '%s %s' % (self.sgenus, self.sspecies)

    def get_abrevname(self):
        abrev = self.sgen.abrev
        if not abrev:
            abrev = self.sgen.genus
        if self.sis_hybrid:
            if self.sinfraspe:
                return '%s %s %s %s %s' % (abrev, self.sis_hybrid, self.sspecies,
                                           self.sinfraspr, self.sinfraspe)
            else:
                return '%s %s %s' % (abrev, self.sis_hybrid, self.sspecies)
        else:
            if self.sinfraspe:
                return '%s %s %s %s' % (abrev, self.sspecies,
                                        self.sinfraspr, self.sinfraspe)
            else:
                return '%s %s' % (abrev, self.sspecies)

    def get_shortaccepted(self):
        if self.is_hybrid:
            if self.infraspe:
                return '%s %s %s %s %s' % (self.genus, self.is_hybrid, self.species, self.infraspr, self.infraspe)
            else:
                return '%s %s %s' % (self.genus, self.is_hybrid, self.species)
        else:
            if self.infraspe:
                return '%s %s %s %s' % (self.genus, self.species, self.infraspr, self.infraspe)
            else:
                return '%s %s' % (self.genus, self.species)


class Hybrid(models.Model):
    # pid                 = models.IntegerField(db_column='pid',primary_key=True)
    pid = models.OneToOneField(
        Species,
        db_column='pid',
        on_delete=models.DO_NOTHING,
        primary_key=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='nathybgen', default=0, on_delete=models.DO_NOTHING)
    source = models.CharField(max_length=10, null=True, blank=True)
    genus = models.CharField(max_length=50, null=True, blank=True)
    species = models.CharField(max_length=50, null=True, blank=True)
    infraspr = models.CharField(max_length=20, null=True, blank=True)
    is_hybrid = models.CharField(max_length=5, null=True, blank=True)
    hybrid_type = models.CharField(max_length=20, null=True, blank=True)
    infraspe = models.CharField(max_length=50, null=True, blank=True)
    author = models.CharField(max_length=200, null=True, blank=True)
    seed_gen = models.ForeignKey(Genus, db_column='seedgen', related_name='natseedgen', null=True,
                                 on_delete=models.DO_NOTHING)
    seed_genus = models.CharField(max_length=50, null=True, blank=True)
    seed_species = models.CharField(max_length=50, null=True, blank=True)
    seed_type = models.CharField(max_length=10, null=True, blank=True)
    seed_id = models.ForeignKey(Species, db_column='seed_id', related_name='natseed_id', null=True, blank=True,
                                on_delete=models.DO_NOTHING)
    pollen_gen = models.ForeignKey(Genus, db_column='pollgen', related_name='natpollgen', null=True,
                                   on_delete=models.DO_NOTHING)
    pollen_genus = models.CharField(max_length=50, null=True, blank=True)
    pollen_species = models.CharField(max_length=50, null=True, blank=True)
    pollen_type = models.CharField(max_length=10, null=True, blank=True)
    pollen_id = models.ForeignKey(Species, db_column='pollen_id', related_name='natpollen_id', null=True, blank=True,
                                  on_delete=models.DO_NOTHING)
    year = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    originator = models.CharField(max_length=100, null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id', related_name='natuser_id', null=True, blank=True, on_delete=models.DO_NOTHING)

    description = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    history = models.TextField(null=True, blank=True)
    culture = models.TextField(null=True, blank=True)
    etymology = models.TextField(null=True, blank=True)

    num_image = models.IntegerField(null=True, blank=True)
    num_ancestor = models.IntegerField(null=True, blank=True)
    num_species_ancestor = models.IntegerField(null=True, blank=True)
    num_descendant = models.IntegerField(null=True, blank=True)
    num_dir_descendant = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.name()

    def registered_seed_name(self):
        name = self.seed_id.name()
        if self.seed_id.textspeciesnamefull() != self.seed_species or self.seed_id.genus != self.seed_genus:
            name = self.seed_genus + ' ' + self.seed_species + ' ' + '(syn)'
        return name

    def registered_seed_name_short(self):
        name = self.seed_id.abrevname()
        if self.seed_id.textspeciesnamefull() != self.seed_species or self.seed_id.genus != self.seed_genus:
            name = self.seed_genus + ' ' + self.seed_species + ' ' + '(syn)'
        return name

    # Used in hybrid-detail parents
    def registered_pollen_name(self):
        name = self.pollen_id.name()
        if self.pollen_id.textspeciesnamefull() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
            name = self.pollen_genus + ' ' + self.pollen_species + ' ' + '(syn)'
        return name

    def registered_pollen_name_short(self):
        name = self.pollen_id.abrevname()
        if self.pollen_id.textspeciesnamefull() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
            name = self.pollen_genus + ' ' + self.pollen_species + ' ' + '(syn)'
        return name

    def registered_seed_name_long(self):
        name = self.seed_id.name()
        if self.seed_id.textspeciesnamefull() != self.seed_species or self.seed_id.genus != self.seed_genus:
            name = self.seed_genus + ' ' + self.seed_species + ' ' + '(syn ' + self.seed_id.textname() + ')'
        return name

    def registered_pollen_name_long(self):
        name = self.pollen_id.name()
        if self.pollen_id.textspeciesnamefull() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
            name = self.pollen_genus + ' ' + self.pollen_species + ' ' + '(syn ' + self.pollen_id.textname() + ')'
        return name

    # def registered_seed_name_long(self):
    #     name = self.seed_genus + ' ' + self.seed_species
    #     if self.seed_id.textspeciesname() != self.seed_species or self.seed_id.genus != self.seed_genus:
    #         name = name + ' ' + '(syn ' + self.seed_id.textname() + ')'
    #     name = '<i>' + name + '</i>'
    #     return name
    #
    # # Used in hybrid_detail/parents name
    # def registered_pollen_name_long(self):
    #     name = self.pollen_genus + ' ' + self.pollen_species
    #     if self.pollen_id.textspeciesname() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
    #         name = name + ' ' + '(syn ' + self.pollen_id.textname() + ')'
    #     name = '<i>' + name + '</i>'
    #     return name

    def seed_status(self):
        if self.seed_id and self.seed_id.textname() != self.seed_genus + ' ' + self.seed_species:
            return 'syn'
        return None

    def pollen_status(self):
        if self.pollen_id and self.pollen_id.textname() != self.pollen_genus + ' ' + self.pollen_species:
            return 'syn'
        return None

    def hybrid_type(self):
        if self.is_hybrid:
            return 'natural'
        else:
            return 'artificial'


class SpcImages(models.Model):
    pid = models.ForeignKey(Accepted, null=False, db_column='pid', related_name='natpid',on_delete=models.DO_NOTHING)
    author = models.ForeignKey(Photographer, db_column='author', related_name='natspcauthor', on_delete=models.DO_NOTHING)
    credit_to = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    quality = models.IntegerField(
                               choices=QUALITY,
                               default=3,
                               )
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
    download_date = models.DateField(null=True, blank=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='natspcgen', null=True, blank=True,on_delete=models.DO_NOTHING)
    is_private = models.BooleanField(null=True, default=False)
    block_id = models.IntegerField(null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id',related_name='natspcuser_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    approved_by = models.ForeignKey(User, db_column='approved_by', related_name='natspc_approved_by', null=True, blank=True,on_delete=models.DO_NOTHING)
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


class HybImages(models.Model):
    form = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    rank = models.IntegerField(choices=RANK_CHOICES,default=5)
    zoom = models.IntegerField(default=0)
    certainty = models.CharField(max_length=20, null=True, blank=True)
    source_file_name = models.CharField(max_length=100, null=True, blank=True)
    awards = models.CharField(max_length=200, null=True, blank=True)
    detail = models.CharField(max_length=20, null=True, blank=True)
    cultivator = models.CharField(max_length=50, null=True, blank=True)
    hybridizer = models.CharField(max_length=50, null=True, blank=True)
    author = models.ForeignKey(Photographer, db_column='author',related_name='nathybauthor', on_delete=models.DO_NOTHING)
    credit_to = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    quality = models.IntegerField(
                               choices=QUALITY,
                               default=3,
                               )
    location = models.CharField(max_length=100, null=True, blank=True)
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    image_url = models.CharField(max_length=500, null=True, blank=True)
    text_data = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=400, null=True, blank=True)
    variation = models.CharField(max_length=50, null=True, blank=True)
    # width = models.FloatField(default=1)
    # height = models.FloatField(default=1)
    image_file = models.CharField(max_length=100, null=True, blank=True)
    image_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
    download_date = models.DateField(null=True, blank=True)
    pid = models.ForeignKey(Hybrid, db_column='pid', verbose_name='grex', null=True, blank=True,on_delete=models.DO_NOTHING)
    spid = models.IntegerField(null=True, blank=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='nathybimggen', null=True, blank=True,on_delete=models.DO_NOTHING)
    is_private = models.BooleanField(null=True, default=False)
    block_id = models.IntegerField(null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id',related_name='nathybuser_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    approved_by = models.ForeignKey(User, db_column='approved_by',  related_name='nathyb_approved_by', null=True, blank=True,on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)
    # upload_by = models.ForeignKey(User, db_column='upload_by', null=True, blank=True,on_delete=models.DO_NOTHING)

    def __str__(self):
        name = self.pid.pid.name()
        if self.variation:
            name = name + ' ' + self.variation
        if self.form:
            name = name + ' ' + self.form
        if self.name:
            name = name + ' ' + self.name
        if self.awards:
            name = name + ' ' + self.awards
        # return '%s %s %s' % (self.author_id, str(self.pid), self.image_file)
        return name

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

    def imgname(self):
        if self.source_file_name:
            myname = self.source_file_name
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

    def image_dir(self):
        # return 'utils/images/hybrid/' + block_id + '/'
        return 'utils/images/hybrid/'

    def thumb_dir(self):
        return 'utils/images/hybrid_thumb/'

    def get_displayname(self):
        if self.credit_to:
            return self.credit_to
        return self.author.displayname

    def get_userid(self):
        author = Photographer.objects.get(author=self.author_id)
        return author.user_id

    # def save(self, *args, **kwargs):
    #     if self.image_file_path:
    #         pilImage = Img.open(BytesIO(self.image_file_path.read()))
    #         for orientation in ExifTags.TAGS.keys():
    #             if ExifTags.TAGS[orientation] == 'Orientation':
    #                 break
    #         exif = dict(pilImage._getexif().items())
    #
    #         if exif[orientation] == 3:
    #             pilImage = pilImage.rotate(180, expand=True)
    #         elif exif[orientation] == 6:
    #             pilImage = pilImage.rotate(270, expand=True)
    #         elif exif[orientation] == 8:
    #             pilImage = pilImage.rotate(90, expand=True)
    #
    #         output = BytesIO()
    #         pilImage.save(output, format='JPEG', quality=75)
    #         output.seek(0)
    #         self.image_file_path = File(output, self.image_file_path.name)
    #
    #     return super(HybImages, self).save(*args, **kwargs)


# class AncestorDescendant(models.Model):
#     class Meta:
#         unique_together = (("did", "aid"),)
#
#     did = models.ForeignKey(Hybrid, null=False, db_column='did', on_delete=models.CASCADE)
#     aid = models.ForeignKey(Species, null=False, db_column='aid', on_delete=models.CASCADE)
#     anctype = models.CharField(max_length=10, default='hybrid')
#     pct = models.FloatField(blank=True, null=True)
#
#     # file = models.CharField(max_length=10, blank=True)
#
#     def __str__(self):
#         hybrid = '%s %s' % (self.did.genus, self.did.species)
#         pct = '%'
#         return '%s %s %s' % (hybrid, self.aid, self.pct)
#
#     def anc_name(self):
#         name = Species.objects.get(pk=self.aid.pid)
#         if name.infraspr:
#             return "%s %s %s %s" % (name.genus, name.species, name.infraspr, name.infraspe)
#         else:
#             return "%s %s" % (name.genus, name.species)
#
#     def anc_abrev(self):
#         # name = Species.objects.get(pk=self.aid.pid)
#         abrev = self.did.abrev
#         return self.did.nameabrev()
#
#     def prettypct(self):
#         # pct = int(self.pct*100)/100
#         percent = '{:5.2f}'.format(float(self.pct))
#
#         return percent.strip("0").strip(".")


# class UploadFile(models.Model):
#     pid = models.ForeignKey(Species, null=True, blank=True, db_column='pid', on_delete=models.DO_NOTHING)
#     author = models.ForeignKey(Photographer, db_column='author', null=True, blank=True, on_delete=models.DO_NOTHING)
#     user_id = models.ForeignKey(User, db_column='user_id', null=True, blank=True, on_delete=models.DO_NOTHING)
#     credit_to = models.CharField(max_length=100, null=True, blank=True)  # should match author_id inPhotography
#     source_url = models.CharField(max_length=1000, null=True, blank=True)
#     source_file_name = models.CharField(max_length=100, null=True, blank=True)
#     name = models.CharField(max_length=100, null=True, blank=True)
#     awards = models.CharField(max_length=200, null=True, blank=True)
#     variation = models.CharField(max_length=50, null=True, blank=True)
#     forma = models.CharField(max_length=50, null=True, blank=True)
#     originator = models.CharField(max_length=50, null=True, blank=True)
#     text_data = models.TextField(null=True, blank=True)
#     description = models.CharField(max_length=100, null=True, blank=True)
#     certainty = models.CharField(max_length=20, null=True, blank=True)
#     type = models.CharField(max_length=20, null=True, blank=True)
#     location = models.CharField(max_length=100, null=True, blank=True)
#     rank = models.IntegerField(choices=RANK_CHOICES, default=0)
#     image_file_path = models.ImageField(upload_to='images/', null=True, blank=True)
#     image_file = models.CharField(max_length=100, null=True, blank=True)
#     is_private = models.BooleanField(null=True, default=False)
#     approved = models.BooleanField(null=True, default=False)
#     compressed = models.BooleanField(null=True, default=False)
#     block_id = models.IntegerField(null=True, blank=True)
#     created_date = models.DateTimeField(auto_now_add=True, null=True)
#     modified_date = models.DateTimeField(auto_now=True, null=True)
#
#     def __str__(self):
#         return self.pid.name()


# @receiver(post_save, sender=UploadFile, dispatch_uid="update_image_profile")
# def update_image(sender, instance, **kwargs):
#     if instance.image_file_path:
#         fullpath = settings.MEDIA_ROOT + '/' + str(instance.image_file_path)
#         rotate_image(fullpath)


# class SpcImages(models.Model):
#     pid = models.ForeignKey(Accepted, null=False, db_column='pid', on_delete=models.DO_NOTHING)
#     author = models.ForeignKey(Photographer, db_column='author', on_delete=models.DO_NOTHING)
#     credit_to = models.CharField(max_length=100, null=True, blank=True)
#     status = models.CharField(max_length=10, default='TBD')
#     quality = models.IntegerField(
#         choices=QUALITY,
#         default=3,
#     )
#     name = models.CharField(max_length=100, null=True, blank=True)
#     source_url = models.CharField(max_length=1000, null=True, blank=True)
#     image_url = models.CharField(max_length=500, null=True, blank=True)
#     text_data = models.TextField(null=True, blank=True)
#     certainty = models.CharField(max_length=20, null=True, blank=True)
#     rank = models.IntegerField(choices=RANK_CHOICES, default=5)
#     zoom = models.IntegerField(default=0)
#     form = models.CharField(max_length=50, null=True, blank=True)
#     source_file_name = models.CharField(max_length=100, null=True, blank=True)
#     spid = models.IntegerField(null=True, blank=True)
#     awards = models.CharField(max_length=200, null=True, blank=True)
#     description = models.CharField(max_length=100, null=True, blank=True)
#     variation = models.CharField(max_length=50, null=True, blank=True)
#     location = models.CharField(max_length=100, null=True, blank=True)
#     type = models.CharField(max_length=20, null=True, blank=True)
#     # width = models.FloatField(default=1)
#     # height = models.FloatField(default=1)
#     image_file = models.CharField(max_length=100, null=True, blank=True)
#     image_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
#     download_date = models.DateField(null=True, blank=True)
#     # gen = models.ForeignKey(Genus, null=True, blank=True, db_column='gen',on_delete=models.DO_NOTHING)
#     # gen = models.IntegerField(null=True, blank=True)
#     gen = models.ForeignKey(Genus, db_column='gen', null=True, blank=True, on_delete=models.DO_NOTHING)
#     is_private = models.BooleanField(null=True, default=False)
#     block_id = models.IntegerField(null=True, blank=True)
#     user_id = models.ForeignKey(User, db_column='user_id', null=True, blank=True, on_delete=models.DO_NOTHING)
#     approved_by = models.ForeignKey(User, db_column='approved_by', related_name='spc_approved_by', null=True,
#                                     blank=True, on_delete=models.DO_NOTHING)
#     created_date = models.DateTimeField(auto_now_add=True, null=True)
#     modified_date = models.DateTimeField(auto_now=True, null=True)
#
#     # upload_by = models.ForeignKey(User, db_column='upload_by', null=True, blank=True,on_delete=models.DO_NOTHING)
#
#     def __str__(self):
#         return self.pid.pid.textname()
#
#     def imgname(self):
#         if self.source_file_name:
#             myname = '<i>%s</i>' % (self.source_file_name)
#         else:
#             myname = self.pid.pid.abrevname()
#         if self.variation:
#             myname = '%s %s ' % (myname, self.variation)
#         if self.form:
#             myname = '%s %s form ' % (myname, self.form)
#         if self.certainty:
#             myname = '%s %s ' % (myname, self.certainty)
#         if self.name:
#             myname = "%s '%s' " % (myname, self.name)
#         if self.awards:
#             myname = '%s %s' % (myname, self.awards)
#         return myname
#
#     def imginfo(self):
#         myname = ''
#         if self.variation:
#             myname = '%s %s ' % (myname, self.variation)
#         if self.form:
#             myname = '%s %s form ' % (myname, self.form)
#         if self.certainty:
#             myname = '%s %s ' % (myname, self.certainty)
#         if self.name:
#             myname = "%s '%s' " % (myname, self.name)
#         if self.awards:
#             myname = '%s %s' % (myname, self.awards)
#         return myname
#
#     def fullimgname(self):
#         if self.source_file_name:
#             myname = self.source_file_name
#         else:
#             myname = self.pid.pid
#         if self.variation:
#             myname = '%s %s ' % (myname, self.variation)
#         if self.form:
#             myname = '%s %s form ' % (myname, self.form)
#         if self.certainty:
#             myname = '%s %s ' % (myname, self.certainty)
#         if self.name:
#             myname = "%s '%s' " % (myname, self.name)
#         if self.awards:
#             myname = '%s %s' % (myname, self.awards)
#         return myname
#
#     def abrev(self):
#         return '%s' % Genus.objects.get(pk=self.gen_id).abrev
#
#     def web(self):
#         web = Photographer.objects.get(author_id=self.author)
#         return web.web
#
#     # TODO: add block_id
#     def image_dir(self):
#         return 'utils/images/species/'
#         # return 'utils/images/hybrid/' + block_id + '/'
#
#     def thumb_dir(self):
#         return 'utils/images/species_thumb/'
#
#     def get_displayname(self):
#         if self.credit_to:
#             return self.credit_to
#         return self.author.displayname
#
#     def get_userid(self):
#         author = Photographer.objects.get(author=self.author_id)
#         return author.user_id


# class HybImages(models.Model):
#     form = models.CharField(max_length=50, null=True, blank=True)
#     name = models.CharField(max_length=100, null=True, blank=True)
#     rank = models.IntegerField(choices=RANK_CHOICES, default=5)
#     zoom = models.IntegerField(default=0)
#     certainty = models.CharField(max_length=20, null=True, blank=True)
#     source_file_name = models.CharField(max_length=100, null=True, blank=True)
#     awards = models.CharField(max_length=200, null=True, blank=True)
#     detail = models.CharField(max_length=20, null=True, blank=True)
#     cultivator = models.CharField(max_length=50, null=True, blank=True)
#     hybridizer = models.CharField(max_length=50, null=True, blank=True)
#     author = models.ForeignKey(Photographer, db_column='author', on_delete=models.DO_NOTHING)
#     credit_to = models.CharField(max_length=100, null=True, blank=True)
#     status = models.CharField(max_length=10, default='TBD')
#     quality = models.IntegerField(
#         choices=QUALITY,
#         default=3,
#     )
#     location = models.CharField(max_length=100, null=True, blank=True)
#     source_url = models.CharField(max_length=1000, null=True, blank=True)
#     image_url = models.CharField(max_length=500, null=True, blank=True)
#     text_data = models.TextField(null=True, blank=True)
#     description = models.CharField(max_length=400, null=True, blank=True)
#     variation = models.CharField(max_length=50, null=True, blank=True)
#     # width = models.FloatField(default=1)
#     # height = models.FloatField(default=1)
#     image_file = models.CharField(max_length=100, null=True, blank=True)
#     image_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
#     download_date = models.DateField(null=True, blank=True)
#     pid = models.ForeignKey(Hybrid, db_column='pid', verbose_name='grex', null=True, blank=True,
#                             on_delete=models.DO_NOTHING)
#     spid = models.IntegerField(null=True, blank=True)
#     gen = models.ForeignKey(Genus, db_column='gen', null=True, blank=True, on_delete=models.DO_NOTHING)
#     is_private = models.BooleanField(null=True, default=False)
#     block_id = models.IntegerField(null=True, blank=True)
#     user_id = models.ForeignKey(User, db_column='user_id', null=True, blank=True, on_delete=models.DO_NOTHING)
#     approved_by = models.ForeignKey(User, db_column='approved_by', related_name='hyb_approved_by', null=True,
#                                     blank=True, on_delete=models.DO_NOTHING)
#     created_date = models.DateTimeField(auto_now_add=True, null=True)
#     modified_date = models.DateTimeField(auto_now=True, null=True)
#
#     # upload_by = models.ForeignKey(User, db_column='upload_by', null=True, blank=True,on_delete=models.DO_NOTHING)
#
#     def __str__(self):
#         name = self.pid.pid.name()
#         if self.variation:
#             name = name + ' ' + self.variation
#         if self.form:
#             name = name + ' ' + self.form
#         if self.name:
#             name = name + ' ' + self.name
#         if self.awards:
#             name = name + ' ' + self.awards
#         # return '%s %s %s' % (self.author_id, str(self.pid), self.image_file)
#         return name
#
#     def imginfo(self):
#         myname = ''
#         if self.variation:
#             myname = '%s %s ' % (myname, self.variation)
#         if self.form:
#             myname = '%s %s form ' % (myname, self.form)
#         if self.certainty:
#             myname = '%s %s ' % (myname, self.certainty)
#         if self.name:
#             myname = "%s '%s' " % (myname, self.name)
#         if self.awards:
#             myname = '%s %s' % (myname, self.awards)
#         return myname
#
#     def imgname(self):
#         if self.source_file_name:
#             myname = self.source_file_name
#         else:
#             myname = self.pid.pid.abrevname()
#         if self.variation:
#             myname = '%s %s ' % (myname, self.variation)
#         if self.form:
#             myname = '%s %s form ' % (myname, self.form)
#         if self.certainty:
#             myname = '%s %s ' % (myname, self.certainty)
#         if self.name:
#             myname = "%s '%s' " % (myname, self.name)
#         if self.awards:
#             myname = '%s %s' % (myname, self.awards)
#         return myname
#
#     def fullimgname(self):
#         if self.source_file_name:
#             myname = self.source_file_name
#         else:
#             myname = self.pid.pid
#         if self.variation:
#             myname = '%s %s ' % (myname, self.variation)
#         if self.form:
#             myname = '%s %s form ' % (myname, self.form)
#         if self.certainty:
#             myname = '%s %s ' % (myname, self.certainty)
#         if self.name:
#             myname = "%s '%s' " % (myname, self.name)
#         if self.awards:
#             myname = '%s %s' % (myname, self.awards)
#
#         return myname
#
#     def image_dir(self):
#         # return 'utils/images/hybrid/' + block_id + '/'
#         return 'utils/images/hybrid/'
#
#     def thumb_dir(self):
#         return 'utils/images/hybrid_thumb/'
#
#     def get_displayname(self):
#         if self.credit_to:
#             return self.credit_to
#         return self.author.displayname
#
#     def get_userid(self):
#         author = Photographer.objects.get(author=self.author_id)
#         return author.user_id
#
#     # def save(self, *args, **kwargs):
#     #     if self.image_file_path:
#     #         pilImage = Img.open(BytesIO(self.image_file_path.read()))
#     #         for orientation in ExifTags.TAGS.keys():
#     #             if ExifTags.TAGS[orientation] == 'Orientation':
#     #                 break
#     #         exif = dict(pilImage._getexif().items())
#     #
#     #         if exif[orientation] == 3:
#     #             pilImage = pilImage.rotate(180, expand=True)
#     #         elif exif[orientation] == 6:
#     #             pilImage = pilImage.rotate(270, expand=True)
#     #         elif exif[orientation] == 8:
#     #             pilImage = pilImage.rotate(90, expand=True)
#     #
#     #         output = BytesIO()
#     #         pilImage.save(output, format='JPEG', quality=75)
#     #         output.seek(0)
#     #         self.image_file_path = File(output, self.image_file_path.name)
#     #
#     #     return super(HybImages, self).save(*args, **kwargs)


# class Distribution(models.Model):
#     id = models.AutoField(primary_key=True, default=10)
#     pid = models.ForeignKey(Species, on_delete=models.CASCADE, db_column='pid', related_name='dist_pid')
#     gen = models.ForeignKey(Genus, on_delete=models.DO_NOTHING, db_column='gen', related_name='dist_gen', null=True,
#                             blank=True)
#     source = models.CharField(max_length=10, blank=True)
#     continent_id = models.ForeignKey(Continent, db_column='continent_id', null=True, blank=True,
#                                      on_delete=models.DO_NOTHING)
#     region_id = models.ForeignKey(Region, db_column='region_id', null=True, on_delete=models.DO_NOTHING)
#     subregion_code = models.ForeignKey(SubRegion, db_column='subregion_code', null=True, on_delete=models.DO_NOTHING)
#     dist_code = models.CharField(max_length=10, null=True)
#     localregion_code = models.CharField(max_length=10, null=True)
#     localregion_id = models.ForeignKey(LocalRegion, db_column='localregion_id', null=True, blank=True,
#                                        on_delete=models.DO_NOTHING)
#     orig_code = models.CharField(max_length=100, blank=True)
#     dist_status = models.CharField(max_length=10, blank=True)
#     confidence = models.CharField(max_length=10, blank=True)
#     comment = models.CharField(max_length=500, blank=True)
#     created_date = models.DateTimeField(auto_now_add=True, null=True)
#     modified_date = models.DateTimeField(auto_now=True, null=True)
#
#     class Meta:
#         unique_together = (("pid", "region_id", "subregion_code", "localregion_id"),)
#
#     def name(self):
#         name = ''
#         if self.localregion_id and self.localregion_id.id > 0 and self.localregion_id.code != 'OO':
#             name = name + self.localregion_id.name
#             if self.subregion_code:
#                 name = name + ', ' + self.subregion_code.name + ', ' + self.continent_id.name
#         elif self.subregion_code:
#             name = name + self.subregion_code.name + ', ' + self.continent_id.name
#         elif self.region_id:
#             name = name + self.region_id.name
#         elif self.continent_id:
#             name = name + self.continent_id.name
#         return name
#
#     def __str__(self):
#         return self.name()
#
#     def subname(self):
#         return self.subregion_code.name
#
#     def regname(self):
#         return self.region_id.name
#
#     def locname(self):
#         return self.localregion_id.name
#
#     def conname(self):
#         return self.continent_id.name




