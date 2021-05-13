from django import template
# from django.utils.html import conditional_escape
# from django.utils.safestring import mark_safe
import datetime

register = template.Library()

# @register.simple_tag
# def add(a, b):
#     if not a:
#         a = 0
#     if not b:
#         b = 0
#     return a+b

@register.simple_tag
def add(a, b, c=None):
    if not a:
        a = 0
    if not b:
        b = 0
    if not c:
        c = 0
    return a+b+c


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
@register.simple_tag(name="simple_time")
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


import re

class CurrentTimeNode3(template.Node):
    def __init__(self, format_string, var_name):
        self.format_string = format_string
        self.var_name = var_name
    def render(self, context):
        context[self.var_name] = datetime.datetime.now().strftime(self.format_string)
        return ''

@register.tag
def do_current_time(parser, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires arguments" % token.contents.split()[0]
        )
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    format_string, var_name = m.groups()
    if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name
        )
    return CurrentTimeNode3(format_string[1:-1], var_name)


# Passing variables
@register.tag(name="created_date")
def do_format_time(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, date_to_be_formatted, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two arguments" % token.contents.split()[0]
        )
    if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name
        )
    return FormatTimeNode(date_to_be_formatted, format_string[1:-1])

class FormatTimeNode(template.Node):
    def __init__(self, date_to_be_formatted, format_string):
        self.date_to_be_formatted = template.Variable(date_to_be_formatted)
        self.format_string = format_string

    def render(self, context):
        try:
            actual_date = self.date_to_be_formatted.resolve(context)
            return actual_date.strftime(self.format_string)
        except template.VariableDoesNotExist:
            return ''


# Cycle
import itertools
from django import template

def __init__(self, cyclevars):
    self.cyclevars = cyclevars

def render(self, context):
    if self not in context.render_context:
        context.render_context[self] = itertools.cycle(self.cyclevars)
    cycle_iter = context.render_context[self]
    return next(cycle_iter)


# Inclusion tag
def show_results(Family):
    subfamilies = Family.subfamily_set.all()
    return {'subfamilies': subfamilies}



# templates
# < ul >
# < li > {{family_list
# .1.created_date}} < / li >
# < li > { % simple_time
# "%Y/%m/%d %I:%M %p" as the_time %} < p > The
# time is {{the_time}}
# Yes!.< / p > < / li >
# < li > { % gohome %} < / li >
# < li > { % do_current_time
# "%Y-%m-%d %I:%M %p" as my_current_time %}
# < p > The
# current
# time
# here is {{my_current_time}}. < / p >
# < / li >
# < li >
# { % created_date
# family_list
# .1.created_date
# "%Y-%m-%d %I:%M %p" %}
# Created
# date is {{format_time}}
# < / li >
# < li >
# { % created_date
# family_list
# .1.modified_date
# "%Y-%m-%d %I:%M %p" %}
# Modified
# date is {{format_time}}
# < / li >
# < / ul >
