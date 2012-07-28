
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.admin import site
from django.contrib import admin
from django import forms


from models import *

class CouponAdmin(admin.ModelAdmin):
    model = Coupon
    list_per_page = 25
    list_display = ('code', 'percent', 'used', 'used_date')
    ordering = ('-used_date',)


class TransactionAdmin(admin.ModelAdmin):
    model = Transaction
    readonly_fields = ('code', 'user', 'type', 'price', 'status', 'expire_date', 'coupon')
    list_display = ('code', 'user', 'type', 'status')
    list_filter = ('expire_date',)
    list_per_page = 25
    date_hierarchy = 'expire_date'


site.register(Coupon,CouponAdmin)
site.register(Transaction,TransactionAdmin)
