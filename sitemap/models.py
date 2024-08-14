# sitemap/models.py
from django.db import models

class SitemapEntry(models.Model):
    url = models.URLField(unique=True)
    last_modified = models.DateTimeField(auto_now=True)
    change_frequency = models.CharField(max_length=50, choices=[
        ('always', 'Always'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('never', 'Never'),
    ])
    priority = models.FloatField(default=0.5, null=True, blank=True)
    section = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.url