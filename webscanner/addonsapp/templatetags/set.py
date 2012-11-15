
from django import template

from fancy_tag import fancy_tag

register = template.Library()

@fancy_tag(register, True)
def set(context, value):
    return value
