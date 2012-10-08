from django import template

register = template.Library()


@register.filter
def is_not_None(s):
    return s is not None
