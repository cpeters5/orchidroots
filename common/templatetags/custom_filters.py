from django import template

register = template.Library()

@register.filter
def firstletter(value):
    """Returns the first letter of the string."""
    if isinstance(value, str) and value:
        return value[0]
    return ''

@register.simple_tag
def add(a, b, c=None):
    if not a:
        a = 0
    if not b:
        b = 0
    if not c:
        c = 0
    return a+b+c
