
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.admin import site
from django.contrib import admin
from django import forms


from models import *

#class CouponAdmin(admin.ModelAdmin):
    #model = Coupon


#class UsersTest_ContactInline(admin.TabularInline):
    #model = UsersTest_Contact

    #def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        #field = super(UsersTest_ContactInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        #if db_field.name == 'contact':
            #if request.userstest_instance is not None:
                #field.queryset = request.userstest_instance.user.contacts.all()
            #else:
                #field.queryset = field.queryset.none()

        #return field


#class ContactInline(admin.TabularInline):
    #model = Contact


#class DomainInline(admin.TabularInline):
    #model = Domain


#class ProfileInline(admin.StackedInline):
    #model = Profile
    #can_add=0
    #can_delete=0
    #max_num=1
    #extra=0


#class UsersTest_OptionsAdmin(admin.TabularInline):
    #model = UsersTest_Options
    #can_add=0
    #can_delete=0
    #max_num=1
    #extra=0


#class UserWithProfile(OriginalUserAdmin):
    #inlines = [ ProfileInline ,DomainInline, ContactInline]

#class TariffDefTestDefInline(admin.TabularInline):
    #model = TariffDef_TestDef


#class TariffDefAdmin(admin.ModelAdmin):
    #model = TariffDef
    #inlines = [ TariffDefTestDefInline ,]


#class UsersTestAdminForm(forms.ModelForm):
    ##limit values
    #def __init__(self,*a,**b):
        #super(UsersTestAdminForm,self).__init__(*a,**b)
        #self.fields['test_def'].queryset = TariffDef_TestDef.objects.filter(
            #tariff_def=self.instance.user.get_profile().tariff_def)
        #self.fields['domain'].queryset = Domain.objects.filter(
            #user = self.instance.user )
#class UsersTestAddAdminForm(forms.ModelForm):
    ##cannot use limits, do not know for what user ;/
    #def __init__(self,*a,**b):
        #super(UsersTestAddAdminForm,self).__init__(*a,**b)

#class UsersTestAdmin(admin.ModelAdmin):
    #form = UsersTestAdminForm
    #model = UsersTest
    #inlines = [ UsersTest_ContactInline , ]

    #def get_form(self, request, obj=None, **kwargs):
        ## just save obj reference for future processing in Inline
        #request.userstest_instance = obj
        #form = super(UsersTestAdmin, self).get_form(request, obj, **kwargs)
        #if not hasattr(form,'request'):
            #form.request = request
        #return form

    #def add_view(self,request):
        ##for add, use form without limits 
        #self.form = UsersTestAddAdminForm
        #view = super(UsersTestAdmin, self).add_view(request)
        #return view



site.unregister(User)
site.register(User,UserWithProfile)

#site.register(UsersTest,UsersTestAdmin)
#site.register(CurrentTest)
#site.register(TariffDef,TariffDefAdmin)
#site.register(Transaction)
##site.register(Contact)
#site.register(CurrentNotification)
##site.register(Domain)
##site.register(Profile)
#site.register(UsersTest_Options)
#site.register(Coupon,CouponAdmin)
