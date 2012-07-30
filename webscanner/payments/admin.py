
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


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    readonly_fields = ('code', 'user', 'price', 'coupon', 'date_subscribed', 'date_canceled')
    list_display = ('code', 'user')
    list_filter = ('date_subscribed', 'date_canceled')
    list_per_page = 25
    date_hierarchy = 'date_subscribed'

class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    readonly_fields = ('subscription', 'price', 'date_created')
    list_per_page = 25



site.register(Coupon, CouponAdmin)
site.register(Subscription, SubscriptionAdmin)
site.register(Payment, PaymentAdmin)


