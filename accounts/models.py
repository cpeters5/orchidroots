from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.signals import pre_social_login
from django.db import models
from django.conf import settings
from django.shortcuts import redirect
from django.db.models.signals import post_save
from allauth.account.signals import user_signed_up, user_logged_in, email_confirmed
from allauth.account.models import EmailAddress

from django.dispatch import receiver

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
# import uuid


class BaseModel(models.Model):
    # uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True

class Tier(BaseModel):
    tier        = models.IntegerField(primary_key=True)
    max_upload  = models.IntegerField(default=0)
    description = models.CharField(max_length=150, null=True, blank=True)
    def __str__(self):
        return str(self.max_upload)


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, fullname=None, credited_name=None, is_staff=False, is_admin=False, is_active=True):
        if not username:
            raise ValueError("User must have user name")
        if not email:
            raise ValueError("User must have email address")
        if not password:
            raise ValueError("User must have a password")
        user_obj = self.model(
            username = username,
            email = self.normalize_email(email),
            fullname = fullname,
            credited_name = credited_name,
        )
        user_obj.set_password(password)
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.active = is_active
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self, username, password=None):
        email = None
        user_obj = self.create_user(
            username,
            email,
            password=password,
            is_staff=True
        )
        return user_obj

    def create_superuser(self, username, email, password=None):
        user_obj = self.create_user(
            username,
            email,
            password=password,
            is_staff=True,
            is_admin=True
        )
        return user_obj


class User(AbstractBaseUser):
    username = models.CharField(max_length=255, unique=True)
    fullname = models.CharField(max_length=255, null=True)
    email = models.EmailField(verbose_name='email address', max_length=255, null=True,default=None, unique=True,)
    active = models.BooleanField(default=True) # Note, can use user.active
    is_active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False) # a admin user; non super-user can use user.is_staff
    admin = models.BooleanField(default=False) # a superuser can use user.is_superuser
    created_date = models.DateTimeField(auto_now_add=True) # can use user.date_joined
    tier = models.ForeignKey(Tier, null=True, db_column='tier',on_delete=models.SET_NULL)

    credited_name =  models.CharField(max_length=255, null=True)
    specialty =  models.CharField(max_length=255, null=True)
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email'] # Username, Email & Password are required by default.

    def save(self, *args, **kwargs):
        if not self.tier:
            tier = Tier.objects.filter(tier=1).last()
            self.tier = tier
        return super().save(*args, **kwargs)

    def get_email(self):
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.username

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self): # FIXME: is_staff is a lookup field, it should not be overiden
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self): # FIXME: is_admin is a lookup field, it should not be overiden
        "Is the user a admin member?"
        return self.admin

    # @property
    # def is_active(self): # is_active is a django auth special lookup field should not be overiden
    #     "Is the user active?"
    #     return self.active

    def get_author(self):
        author = Profile.objects.get(user_id=self.id)
        return author.current_credit_name

    def add_email_address(self, request, new_email):
        # Add a new email address for the user, and send email confirmation.
        # Old email will remain the primary until the new one is confirmed.
        return EmailAddress.objects.add_email(request, self.user, new_email, confirm=True)

    
@receiver(email_confirmed)
def update_user_email(sender, request, email_address, **kwargs):
    # Once the email address is confirmed, make new email_address primary.
    # This also sets user.email to the new email address.
    # email_address is an instance of allauth.account.models.EmailAddress
    email_address.set_as_primary()
    # Get rid of old email addresses
    stale_addresses = EmailAddress.objects.filter(
        user=email_address.user).exclude(primary=True).delete()
        
class Country(BaseModel):
    # class Meta:
    #     unique_together = (("dist_code", "dist_num", "region"),)
    #     ordering = ['country','region']
    dist_code = models.CharField(max_length=3,primary_key=True)
    dist_num  = models.IntegerField(null=True, blank=True)
    country   = models.CharField(max_length=100, null=True, blank=True)
    region    = models.CharField(max_length=100, null=True, blank=True)
    orig_code = models.CharField(max_length=100, null=True, blank=True)
    uncertainty = models.CharField(max_length=10, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s' % self.country


class Photographer(BaseModel):
    author_id = models.CharField(max_length=50, primary_key=True)
    displayname = models.CharField(max_length=50)
    fullname = models.CharField(max_length=50)
    affiliation = models.CharField(max_length=200, null=True, blank=True)
    url = models.CharField(max_length=400, null=True, blank=True)
    web = models.CharField(max_length=400, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    expertise = models.CharField(max_length=500, null=True)
    # user_id   = models.OneToOneField(User,unique=True, null=True, blank=True, db_column='user_id', related_name='userid', on_delete=models.SET_NULL)
    user_id   =  models.OneToOneField(
        User,
        db_column='user_id',
        null = True,
        on_delete=models.SET_NULL)
        # models.ForeignKey(User, null=True, blank=True, db_column='user_id', related_name='userid', on_delete=models.SET_NULL)

    def get_authid(self):
        return self.author_id

    def __str__(self):
        if self.displayname != self.fullname:
            return '%s (%s)' % (self.displayname, self.fullname)
        return self.fullname

    # def mypriphoto (self):
    #     myimg = SpcImages.objects.filter(rank__gt=0).filter(user_id=self.user_id).count() + \
    #             SpcImages.objects.filter(rank__gt=0).filter(user_id=self.user_id).count() + \
    #             UploadFile.objects.filter(user_id=self.user_id).count()
    #     return '%' % str(myimg)


class Profile(BaseModel):
    user = models.OneToOneField(User, primary_key=True,on_delete=models.CASCADE)
    # fullname = models.CharField(max_length=255,blank=True,null=True)
    confirm_email = models.CharField(max_length=100, blank=True)
    photo_credit_name = models.CharField(max_length=100, blank=True)
    current_credit_name = models.OneToOneField(Photographer, blank=True, null=True, on_delete=models.SET_NULL)
    specialty = models.CharField(max_length=500, null=True, blank=True)
    portfolio_site = models.URLField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    profile_pic_url = models.URLField(null=True, blank=True)
    # country = models.CharField(max_length=10, null=True, blank=True)
    country = models.ForeignKey(Country, db_column='country', on_delete=models.SET_NULL, null=True, blank=True)
    approved = models.BooleanField( blank=True, default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    def __str__(self):
        if self.user.fullname:
            return self.user.fullname
        else:
            return self.user.username


class Donation(BaseModel):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    amount = models.FloatField()
    payment_type = models.CharField(max_length=20,blank=True,null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Partner(BaseModel):
    partner_id = models.CharField(max_length=50, primary_key=True)
    author = models.ForeignKey(Photographer, db_column='author', on_delete=models.SET_NULL, null=True, blank=True)
    displayname = models.CharField(max_length=50)
    fullname = models.CharField(max_length=50)
    logo = models.CharField(max_length=50, blank=True)
    banner = models.CharField(max_length=50, blank=True)
    banner_color = models.CharField(max_length=50, blank=True)
    affiliation = models.CharField(max_length=200, null=True, blank=True)
    url = models.CharField(max_length=200, null=True, blank=True)
    web = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=10, default='TBD')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    information = models.TextField(null=True)
    user_id   =  models.OneToOneField(
        User,
        db_column='user_id',
        null = True,
        on_delete=models.SET_NULL)

    def __str__(self):
        if self.displayname != self.fullname:
            return '%s' % (self.displayname)
        return self.fullname


