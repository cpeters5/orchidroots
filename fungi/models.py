from django.db import models
from django.db.models import Q, Manager
from django.dispatch import receiver
from PIL import Image as Img
from PIL import ExifTags
from django.conf import settings
from accounts.models import User, Photographer
from common.models import Family, Subfamily, Tribe, Subtribe, Country, Region, Continent, SubRegion, LocalRegion
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

STATUS_CHOICES = [('accepted', 'accepted'), ('unplaced', 'unplaced'), ('published', 'published'), ('synonym', 'synonym')]

TYPE_CHOICES = [('species', 'species'), ('hybrid', 'hybrid')]


class Genus(models.Model):
    pid = models.BigAutoField(primary_key=True)
    orig_pid = models.CharField(max_length=20, null=True, blank=True)
    is_hybrid = models.CharField(max_length=1, null=True)
    genus = models.CharField(max_length=50, default='', unique=True)
    author = models.CharField(max_length=200, blank=True)
    citation = models.CharField(max_length=200, default='')
    cit_status = models.CharField(max_length=20, null=True)
    family = models.ForeignKey(Family, null=True, blank=True, db_column='family', related_name='funfamily', on_delete=models.DO_NOTHING)
    subfamily = models.ForeignKey(Subfamily, null=True, blank=True, db_column='subfamily', related_name='funsubfamily', on_delete=models.DO_NOTHING)
    tribe = models.ForeignKey(Tribe, null=True, blank=True, db_column='tribe', related_name='funtribe', on_delete=models.DO_NOTHING)
    subtribe = models.ForeignKey(Subtribe, null=True, blank=True, db_column='subtribe', related_name='funsubtribe', on_delete=models.DO_NOTHING)
    is_succulent = models.BooleanField(null=True, default=False)
    is_carnivorous = models.BooleanField(null=True, default=False)
    is_extinct = models.BooleanField(null=True, default=False)
    is_parasitic = models.BooleanField(null=True, default=False)
    status = models.CharField(max_length=20, blank=True)
    type = models.CharField(max_length=20, default='')
    common_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True)
    location = models.TextField(null=True)
    distribution = models.TextField(null=True)
    text_data = models.TextField(null=True)
    source = models.CharField(max_length=50, blank=True)
    abrev = models.CharField(max_length=50, blank=True)
    year = models.IntegerField(null=True, blank=True)
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

    def get_application(self):
        return self.family.application

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

    def get_best_img(self):
        img = SpcImages.objects.filter(gen=self.pid).filter(image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')

        if img.count() > 0:
            img = img[0:1][0]
            return img
        return None


class Gensyn(models.Model):
    # pid = models.BigIntegerField(null=True, blank=True)
    pid = models.OneToOneField(
        Genus,
        db_column='pid',
        on_delete=models.CASCADE,
        primary_key=True)
    acc = models.ForeignKey(Genus, verbose_name='genus', related_name='fgen_id', null=True, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid


class GenusRelation(models.Model):
    gen = models.OneToOneField(Genus, db_column='gen',primary_key=True,on_delete=models.CASCADE)
    genus = models.CharField(max_length=50, default='')
    parentlist = models.CharField(max_length=500, null=True)
    formula = models.CharField(max_length=500, null=True)

    def get_parentlist(self):
        x = self.parentlist.split('|')
        return x


class Species(models.Model):
    # enfoirce uniqueness when all records are filled.
    # Otherwise, use script to ensure uniqueness if not null.
    # class Meta:
    #     unique_together = (("source", "orig_pid"),)
    pid = models.BigAutoField(primary_key=True)
    orig_pid = models.CharField(max_length=20, null=True, blank=True)
    source = models.CharField(max_length=10, blank=True)
    genus = models.CharField(max_length=50, null=True, blank=True)
    is_hybrid = models.CharField(max_length=1, null=True)
    species = models.CharField(max_length=50, null=True, blank=True)
    infraspr = models.CharField(max_length=20, null=True, blank=True)
    infraspe = models.CharField(max_length=50, null=True, blank=True)
    author = models.CharField(max_length=200, blank=True)
    originator = models.CharField(max_length=100, blank=True)
    binomial = models.CharField(max_length=500, blank=True)
    family = models.ForeignKey(Family, null=True, db_column='family', related_name='spcfunfamily', on_delete=models.DO_NOTHING)
    citation = models.CharField(max_length=200)
    is_poisonous = models.BooleanField(null=True, default=False)
    is_edible = models.BooleanField(null=True, default=False)
    is_parasitic = models.BooleanField(null=True, default=False)
    cit_status = models.CharField(max_length=20, null=True)
    conservation_status = models.CharField(max_length=20, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='')
    year = models.IntegerField(null=True, blank=True)
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
    gen = models.ForeignKey(Genus, db_column='gen', related_name='funpoolgen', default=0, on_delete=models.DO_NOTHING)
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

    def binomial_it(self):
        if self.type == 'species':
            return '<i>%s</i>' % (self.binomial)
        else:
            return self.binomial

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
            spc = '%s %s' % (spc, self.infraspr)
        if self.infraspe:
            spc = '%s <i>%s</i>' % (spc, self.infraspe)
        return spc

    # def textspeciesname(self):
    #     spc = re.sub('Memoria', 'Mem.', self.species.rstrip())
    #     if self.infraspr:
    #         spc = '%s <i>%s</i>' % (spc, self.infraspr)
    #     if self.infraspe:
    #         spc = '%s <i>%s</i>' % (name, self.infraspe)
    #     if self.is_hybrid:
    #         spc = '%s %s' % (self.is_hybrid, spc)
    #     return spc

    def textspeciesnamefull(self):
        spc = self.species.rstrip()
        if self.infraspr:
            spc = '%s <i>%s</i>' % (spc, self.infraspr)
        if self.infraspe:
            spc = '%s <i>%s</i>' % (spc, self.infraspe)
        if self.is_hybrid:
            spc = '%s %s' % (self.is_hybrid, spc)
        return spc

    def textname(self):
        spc = re.sub('Memoria', 'Mem.', self.species.rstrip())
        if self.infraspr:
            spc = '%s <i>%s</i>' % (spc, self.infraspr)
        if self.infraspe:
            spc = '%s <i>%s</i>' % (name, self.infraspe)
        if self.is_hybrid:
            spc = '%s %s' % (self.is_hybrid, spc)

        return '%s %s' % (self.genus, spc)

    def name(self):
        return '<i>%s</i> %s' % (self.genus, self.speciesname())

    def abrevname(self):
        if self.gen.abrev:
            name = '<i>%s</i> %s' % (self.gen.abrev, self.speciesname())
        else:
            name = '<i>%s</i> %s' % (self.genus, self.speciesname())
        return name

    def get_species(self):
        name = '%s' % (self.species)
        if self.is_hybrid:
            name = '%s %s' % (self.is_hybrid, name)
        if self.infraspr:
            name = '%s %s' % (name, self.infraspr)
        if self.infraspe:
            name = '%s %s' % (name, self.infraspe)
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

    def grex(self):
        if self.infraspr:
            name = name + ' ' + str(self.infraspr)
        if self.infraspe:
            name = name + str(self.infraspe)
        return name

    def sourceurl(self):
        if self.source == 'AlgaeBase' and self.orig_pid:
            return "https://www.algaebase.org/search/species/detail/?species_id=" + self.orig_pid
        elif self.source == 'APNI' and self.orig_pid:
            return "https://biodiversity.org.au/nsl/services/rest/name/apni/" + self.orig_pid + "/api/apni-format"
        elif self.source == 'EOL' and self.orig_pid:
            return "https://eol.org/pages/" + self.orig_pid
        elif self.source == 'FUNG' and self.orig_pid:
            return "http://www.indexfungorum.org/names/NamesRecord.asp?RecordID=" + self.orig_pid
        elif self.source == 'GBIF' and self.orig_pid:
            return "https://www.gbif.org/species/" + self.orig_pid
        elif self.source == 'IPNI' and self.orig_pid:
            return "https://www.ipni.org/n/" + self.orig_pid
        elif self.source == 'ITIS' and self.orig_pid:
            return "https://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value=" + self.orig_pid
        elif self.source == 'Kew':
            return "https://wcsp.science.kew.org/namedetail.do?name_id=" + str(self.pid)
        elif self.source == 'NCBI' and self.orig_pid:
            return "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=" + self.orig_pid
        elif self.source == 'PL' and self.orig_pid:
            return "http://www.theplantlist.org/tpl1.1/record/" + self.orig_pid
        elif self.source == 'POWO' and self.orig_pid:
            return "https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:" + self.orig_pid
        elif self.source == 'Tropicos' and self.orig_pid:
            return "http://http://legacy.tropicos.org/Name/" + self.orig_pid
        else:
            return None

    def get_best_img(self):
        img = SpcImages.objects.filter(pid=self.pid).filter(image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')

        if img.count() > 0:
            img = img[0:1][0]
            return img
        return None

    def get_best_img_by_author(self, author):
        img = SpcImages.objects.filter(pid=self.pid).filter(author_id=author).filter(
                image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')

        if img.count() > 0:
            img = img[0:1][0]
            return img
        return None

    def get_num_img_by_author(self, author):
        if self.type == 'species':
            img = SpcImages.objects.filter(pid=self.pid).filter(author_id=author).filter(image_file__isnull=False).filter(rank=0)
        else:
            img = HybImages.objects.filter(pid=self.pid).filter(author_id=author).filter(image_file__isnull=False).filter(rank=0)
        upl = UploadFile.objects.filter(pid=self.pid).filter(author=author)
        return len(img) + len(upl)


class FungiManager(Manager):
    def search(self, query):
        return self.raw(
            'SELECT * FROM fungi_accepted WHERE MATCH(binomial, common_name) AGAINST (%s IN NATURAL LANGUAGE MODE)',
            [query]
        )

class Accepted(models.Model):
    pid = models.OneToOneField(
        Species,
        db_column='pid',
        on_delete=models.CASCADE,
        primary_key=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='fungen_id', null=True, blank=True, on_delete=models.DO_NOTHING)
    binomial = models.CharField(max_length=150, null=True)
    distribution = models.TextField(blank=True)
    location = models.TextField(blank=True)
    introduced = models.TextField(blank=True)
    is_type = models.BooleanField(null=True, default=False)
    physiology = models.CharField(max_length=200, null=True, blank=True)
    url = models.CharField(max_length=200, null=True, blank=True)
    url_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    common_name = models.CharField(max_length=500, null=True, blank=True)
    common_name_search = models.CharField(max_length=500, null=True, blank=True)
    local_name = models.CharField(max_length=100, null=True, blank=True)
    bloom_month = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    fragrance = models.CharField(max_length=50, null=True, blank=True)
    altitude = models.CharField(max_length=50, null=True, blank=True)

    # history = models.TextField(null=True, blank=True)
    # analysis = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    etymology = models.TextField(null=True, blank=True)
    culture = models.TextField(null=True, blank=True)

    subgenus = models.CharField(max_length=50, null=True, blank=True)
    section = models.CharField(max_length=50, null=True, blank=True)
    subsection = models.CharField(max_length=50, null=True, blank=True)
    series = models.CharField(max_length=50, null=True, blank=True)

    num_image = models.IntegerField(null=True, blank=True)
    num_descendant = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)
    operator = models.ForeignKey(User, db_column='operator', related_name='funoperator', null=True, on_delete=models.DO_NOTHING)

    objects = FungiManager()

    def __str__(self):
        return self.pid.name()

    def get_best_img(self):
        spid_list = Synonym.objects.filter(acc_id=self.pid).values_list('spid')
        img = SpcImages.objects.filter(Q(pid=self.pid) | Q(pid__in=spid_list)).filter(image_file__isnull=False).filter(rank__lt=7).order_by(
                'quality', '-rank', '?')
        if len(img) > 0:
            img = img[0:1][0]
            return img
        return None


class Hybrid(models.Model):
    pid = models.OneToOneField(
        Species,
        db_column='pid',
        on_delete=models.DO_NOTHING,
        primary_key=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='funhybgen', default=0, on_delete=models.DO_NOTHING)
    source = models.CharField(max_length=10, null=True, blank=True)
    binomial = models.CharField(max_length=150, null=True)
    is_hybrid = models.CharField(max_length=5, null=True, blank=True)
    hybrid_type = models.CharField(max_length=20, null=True, blank=True)
    author = models.CharField(max_length=200, null=True, blank=True)
    # seed_gen = models.BigIntegerField(null=True, blank=True)
    seed_gen = models.ForeignKey(Genus, db_column='seedgen', related_name='funseedgen', null=True,
                                 on_delete=models.DO_NOTHING)
    seed_genus = models.CharField(max_length=50, null=True, blank=True)
    seed_species = models.CharField(max_length=50, null=True, blank=True)
    seed_type = models.CharField(max_length=10, null=True, blank=True)
    seed_id = models.ForeignKey(Species, db_column='seed_id', related_name='funseed_id', null=True, blank=True,
                                on_delete=models.DO_NOTHING)
    # pollen_gen = models.BigIntegerField(null=True, blank=True)
    pollen_gen = models.ForeignKey(Genus, db_column='pollgen', related_name='funpollgen', null=True,
                                   on_delete=models.DO_NOTHING)
    pollen_genus = models.CharField(max_length=50, null=True, blank=True)
    pollen_species = models.CharField(max_length=50, null=True, blank=True)
    pollen_type = models.CharField(max_length=10, null=True, blank=True)
    pollen_id = models.ForeignKey(Species, db_column='pollen_id', related_name='funpollen_id', null=True, blank=True,
                                  on_delete=models.DO_NOTHING)
    year = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    originator = models.CharField(max_length=100, null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id', related_name='funuser_id1', null=True, blank=True, on_delete=models.DO_NOTHING)

    description = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    # history = models.TextField(null=True, blank=True)
    culture = models.TextField(null=True, blank=True)
    etymology = models.TextField(null=True, blank=True)

    num_image = models.IntegerField(null=True, blank=True)
    num_ancestor = models.IntegerField(null=True, blank=True)
    num_species_ancestor = models.IntegerField(null=True, blank=True)
    num_descendant = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.name()

    def registered_seed_name(self):
        if self.seed_id:
            name = self.seed_id.name()
            if self.seed_id.textspeciesnamefull() != self.seed_species or self.seed_id.genus != self.seed_genus:
                name = self.seed_genus + ' ' + self.seed_species + ' ' + '(syn)'
            return name
        return None

    def registered_seed_name_short(self):
        if self.seed_id:
            name = self.seed_id.abrevname()
            if self.seed_id.textspeciesnamefull() != self.seed_species or self.seed_id.genus != self.seed_genus:
                name = self.seed_genus + ' ' + self.seed_species + ' ' + '(syn)'
            return name
        return None

    # Used in hybrid-detail parents
    def registered_pollen_name(self):
        if self.pollen_id:
            name = self.pollen_id.name()
            if self.pollen_id.textspeciesnamefull() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
                name = self.pollen_genus + ' ' + self.pollen_species + ' ' + '(syn)'
            return name
        return None

    def registered_pollen_name_short(self):
        if self.pollen_id:
            name = self.pollen_id.abrevname()
            if self.pollen_id.textspeciesnamefull() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
                name = self.pollen_genus + ' ' + self.pollen_species + ' ' + '(syn)'
            return name
        return None

    def registered_seed_name_long(self):
        if self.seed_id:
            name = self.seed_id.name()
            if self.seed_id.textspeciesnamefull() != self.seed_species or self.seed_id.genus != self.seed_genus:
                name = self.seed_genus + ' ' + self.seed_species + ' ' + '(syn ' + self.seed_id.textname() + ')'
            return name
        return None

    def registered_pollen_name_long(self):
        if self.pollen_id:
            name = self.pollen_id.name()
            if self.pollen_id.textspeciesnamefull() != self.pollen_species or self.pollen_id.genus != self.pollen_genus:
                name = self.pollen_genus + ' ' + self.pollen_species + ' ' + '(syn ' + self.pollen_id.textname() + ')'
            return name
        return None

    def hybrid_type(self):
        if self.is_hybrid:
            return 'natural'
        else:
            return 'artificial'


class AncestorDescendant(models.Model):
    class Meta:
        unique_together = (("did", "aid"),)

    did = models.ForeignKey(Hybrid, null=False, db_column='did', related_name='fundid',on_delete=models.CASCADE)
    aid = models.ForeignKey(Species, null=False, db_column='aid', related_name='funaid',on_delete=models.CASCADE)
    anctype = models.CharField(max_length=10, default='hybrid')
    pct = models.FloatField(blank=True, null=True)
    # file = models.CharField(max_length=10, blank=True)

    def __str__(self):
        hybrid = '%s %s' % (self.did.genus, self.did.species)
        pct = '%'
        return '%s %s %s' % (hybrid, self.aid, self.pct)

    def prettypct(self):
        # pct = int(self.pct*100)/100
        percent = '{:5.2f}'.format(float(self.pct))

        return percent.strip("0").strip(".")


class Location(models.Model):
    dist = models.CharField(max_length=200,unique=True, blank=True)
    name = models.CharField(max_length=200,blank=True)

    def __str__(self):
        return self.dist


class Distribution(models.Model):
    pid = models.ForeignKey(Species, on_delete=models.DO_NOTHING,db_column='pid', default='', related_name='fundist_pid')
    dist = models.ForeignKey(Location, db_column='dist', default='', on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = (("pid", "dist"),)


class Synonym(models.Model):
    spid = models.OneToOneField(
        Species,
        related_name='funspid',
        db_column='spid',
        on_delete=models.CASCADE,
        primary_key=True)
    acc = models.ForeignKey(Species, verbose_name='accepted genus', related_name='funaccid', on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    # def __str__(self):
    #     return self.spid.name()


class SpcImages(models.Model):
    pid = models.ForeignKey(Species, null=False, db_column='pid', related_name='funspcimgpid',on_delete=models.DO_NOTHING)
    binomial = models.CharField(max_length=100, null=True, blank=True)
    author = models.ForeignKey(Photographer, db_column='author', related_name='funspcimgauthor', on_delete=models.DO_NOTHING)
    credit_to = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    quality = models.IntegerField(choices=QUALITY, default=3,)
    name = models.CharField(max_length=100, null=True, blank=True)
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    image_url = models.CharField(max_length=500, null=True, blank=True)
    text_data = models.TextField(null=True, blank=True)
    certainty = models.CharField(max_length=20, null=True, blank=True)
    rank = models.IntegerField(choices=RANK_CHOICES,default=5)
    form = models.CharField(max_length=50, null=True, blank=True)
    source_file_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    variation = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=20, null=True, blank=True)
    image_file = models.CharField(max_length=100, null=True, blank=True)
    image_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
    family = models.ForeignKey(Family, db_column='family', related_name='funpoolspcfamily', on_delete=models.DO_NOTHING)
    genus = models.CharField(max_length=50)
    species = models.CharField(max_length=50, null=True, blank=True)
    gen = models.ForeignKey(Genus, db_column='gen', related_name='poolspcgen', null=True, blank=True,on_delete=models.DO_NOTHING)
    download_date = models.DateField(null=True, blank=True)
    block_id = models.IntegerField(null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id',related_name='funpooluser_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    approved_by = models.ForeignKey(User, db_column='approved_by', related_name='funpoolapproved_by', null=True, blank=True,on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.textname()

    def imgname(self):
        if self.source_file_name:
            myname = '<i>%s</i>' % (self.source_file_name)
        else:
            myname = self.pid.abrevname()
        if self.variation:
            myname = '%s %s ' % (myname, self.variation)
        if self.form:
            myname = '%s %s form ' % (myname, self.form)
        if self.certainty:
            myname = '%s %s ' % (myname, self.certainty)
        if self.name:
            myname = "%s '%s' " % (myname, self.name)
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
        return myname

    def fullimgname(self):
        if self.source_file_name:
            myname = self.source_file_name
        else:
            myname = self.pid
        if self.variation:
            myname = '%s %s ' % (myname, self.variation)
        if self.form:
            myname = '%s %s form ' % (myname, self.form)
        if self.certainty:
            myname = '%s %s ' % (myname, self.certainty)
        if self.name:
            myname = "%s '%s' " % (myname, self.name)
        return myname

    def abrev(self):
        return '%s' % Genus.objects.get(pk=self.gen_id).abrev

    def web(self):
        web = Photographer.objects.get(author_id=self.author)
        return web.web

    # TODO: add block_id
    def image_dir(self):
        return 'utils/images/' + self.family.family + '/'
        # return 'utils/images/hybrid/' + block_id + '/'

    def thumb_dir(self):
        return 'utils/thumbs/' + self.family.family + '/'

    def get_displayname(self):
        if self.credit_to:
            return self.credit_to
        return self.author.displayname

    def get_userid(self):
        author = Photographer.objects.get(author=self.author_id)
        return author.user_id


class Video(models.Model):
    pid = models.ForeignKey(Species, null=False, db_column='pid', related_name='funvideopid',on_delete=models.DO_NOTHING)
    binomial = models.CharField(max_length=100, null=True, blank=True)
    author = models.ForeignKey(Photographer, db_column='author', related_name='funvideoauthor', on_delete=models.DO_NOTHING)
    credit_to = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    quality = models.IntegerField(choices=QUALITY, default=3,)
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    video_url = models.CharField(max_length=500, null=True, blank=True)
    text_data = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    video_file = models.CharField(max_length=100, null=True, blank=True)
    video_file_path = models.ImageField(upload_to='utils/images/photos', null=True, blank=True)
    family = models.ForeignKey(Family, db_column='family', related_name='funvideofamily', on_delete=models.DO_NOTHING)
    download_date = models.DateField(null=True, blank=True)
    user_id = models.ForeignKey(User, db_column='user_id',related_name='funvideouser_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    approved_by = models.ForeignKey(User, db_column='approved_by', related_name='funvideoapproved_by', null=True, blank=True,on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.textname()

    def video_dir(self):
        return 'utils/images/' + self.family.family + '/'
        # return 'utils/images/hybrid/' + block_id + '/'

    # def get_image_file_path(self):
    #     return 'utils/images/' + self.family.family + '/' + self.image_file
    #

    def get_displayname(self):
        if self.credit_to:
            return self.credit_to
        return self.author.displayname

    def get_userid(self):
        author = Photographer.objects.get(author=self.author_id)
        return author.user_id


class UploadFile(models.Model):
    pid        = models.ForeignKey(Species, null=True, blank=True, db_column='pid', related_name='funpid',on_delete=models.DO_NOTHING)
    author     = models.ForeignKey(Photographer, db_column='author', related_name='funauthor', null=True, blank=True,on_delete=models.DO_NOTHING)
    user_id    = models.ForeignKey(User, db_column='user_id', related_name='funuser_id', null=True, blank=True,on_delete=models.DO_NOTHING)
    credit_to  = models.CharField(max_length=100, null=True, blank=True)    #should match author_id inPhotography
    source_url = models.CharField(max_length=1000, null=True, blank=True)
    source_file_name = models.CharField(max_length=100, null=True, blank=True)
    name        = models.CharField(max_length=100, null=True, blank=True)
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
    approved    = models.BooleanField(null=True, default=False)
    compressed  = models.BooleanField(null=True, default=False)
    block_id    = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.pid.name()

