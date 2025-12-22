from django import template

register = template.Library()

@register.filter(name='dict_key')
def dict_key(dictionary, key):
    """Returns the value for the given key from a dictionary."""
    return dictionary.get(key)