from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Returns the string split by delimiter.
    """
    if value is None:
        return []
    return value.split(delimiter)

@register.filter
def strip(value):
    """
    Returns the string with whitespace stripped.
    """
    if value is None:
        return ''
    return value.strip() 