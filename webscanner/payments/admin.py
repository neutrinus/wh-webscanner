
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

class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    readonly_fields = ('code', 'user', 'price', 'coupon', 'date_created', 'date_paid')

    list_per_page = 25
    date_hierarchy = 'date_created'
    list_filter = ('date_created', 'date_paid')

site.register(Coupon, CouponAdmin)
site.register(Payment, PaymentAdmin)


