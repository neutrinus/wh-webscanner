
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.admin import site
from django.contrib import admin
from django import forms

from models import *

#site.unregister(User)
#site.register(User,UserWithProfile)

site.register(Tests)
site.register(CommandQueue)
site.register(Results)

