from django import template
# from django.utils.html import conditional_escape
# from django.utils.safestring import mark_safe
import datetime

register = template.Library()

@register.filter(expects_localtime=True)
def businesshours(value):
    try:
        return 9 <= value.hour < 17
    except AttributeError:
        return ''

@register.filter
def cut(value, arg):
    return value.replace(arg, 'y')

@register.filter(is_safe=True)
def add_xx(value):
    return '%sxx' % value


# Simple tags
@register.simple_tag
def current_time(format_string):
    return datetime.datetime.now().strftime(format_string)
# {% current_time "%Y-%m-%d %I:%M %p" as the_time %}
# <p>The time is {{ the_time }}.</p>

# Inclusion tags
@register.inclusion_tag('utils/gohome.html', takes_context=True)
def gohome(context):
    # choices = core.choice_set.all()
    return {
        'link': context['home_link'],
        'title': context['title'],
    }