from django import template

register = template.Library()

def get_verbose_name(object, fieldname):
    try:
        return object._meta.get_field_by_name(fieldname)[0].verbose_name
    except:
        return None

register.simple_tag(get_verbose_name)
