
from django import template
from django.core.signing import Signer

from fancy_tag import fancy_tag

register = template.Library()

@fancy_tag(register, True)
def sign(context, value):
    return Signer().sign(value)
