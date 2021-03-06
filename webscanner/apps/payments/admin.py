
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.admin import site
from django.contrib import admin
from django import forms

from models import *

class CouponAdmin(admin.ModelAdmin):
    model = Coupon
    list_per_page = 100
    list_display = ('code', 'percent', 'used', 'used_date')
    ordering = ('-used_date',)
    list_filter = ('used', 'used_date')
    search_fields = ['code', 'percent']

class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    readonly_fields = ('code', 'user', 'price', 'credits', 'coupon', 'date_created', 'is_paid', 'date_paid')
    list_per_page = 100
    date_hierarchy = 'date_created'
    ordering = ('-date_created',)
    list_filter = ('date_paid', 'is_paid')
    search_fields = ['coupon__code', 'code', 'user__email', 'user__username', 'price']
    list_display = ('user', 'price', 'code', 'coupon', 'is_paid', 'date_paid')

class CreditsPricingPlanAdmin(admin.ModelAdmin):
    model = CreditsPricingPlan
    ordering = ('name',)
    list_display = ('name', 'price', 'credits', 'is_active')
    list_filter = ( 'is_active',)

site.register(Coupon, CouponAdmin)
site.register(Payment, PaymentAdmin)
site.register(CreditsPricingPlan, CreditsPricingPlanAdmin)


